#ifndef MYRECURSIVEASTVISITOR_H
#define MYRECURSIVEASTVISITOR_H

#include <clang/AST/RecursiveASTVisitor.h>
#include <clang/Basic/FileEntry.h>
#include <clang/Basic/SourceManager.h>
#include <clang/Frontend/CompilerInstance.h>
#include <clang/Lex/Preprocessor.h>
#include <fstream>
#include <llvm/ADT/SetVector.h>
#include <llvm/Support/JSON.h>
#include <set>
#include <unistd.h>

using namespace clang;

typedef std::map<SourceLocation, std::vector<SourceRange>> MacroExpansionMap;

class MacroExpansionRecorder : public PPCallbacks {
  // const Preprocessor &PP;
  // SourceManager &SM;
  MacroExpansionMap &MEM;

public:
  explicit MacroExpansionRecorder(const Preprocessor &PP, SourceManager &SM, MacroExpansionMap &MEM)
      : /*PP(PP), SM(SM),*/ MEM(MEM) {}

  void MacroExpands(const Token &MacroName, const MacroDefinition &MD, SourceRange Range,
                    const MacroArgs *Args) override {
    // Ignore annotation tokens like: _Pragma("pack(push, 1)")
    if (MacroName.getIdentifierInfo()->getName() == "_Pragma")
      return;

    // Record a Mapping of (original) expansion Location to all macro
    // source ranges that were used.
    auto MI = MD.getMacroInfo();
    MEM[MacroName.getLocation()].push_back(SourceRange(MI->getDefinitionLoc(), MI->getDefinitionEndLoc()));
  }
};

class MyRecursiveASTVisitor : public RecursiveASTVisitor<MyRecursiveASTVisitor> {
  using Inherited = clang::RecursiveASTVisitor<MyRecursiveASTVisitor>;
  MacroExpansionMap &MEM;

public:
  /// Configure the RecursiveASTVisitor
  bool shouldWalkTypesOfTypeLocs() const { return false; }

  explicit MyRecursiveASTVisitor(ASTContext *Context, MacroExpansionMap &MEM, const CompilerInstance &CI)
      : MEM(MEM), Context(Context), SM(Context->getSourceManager()), CI(CI) {}

  /// For some special nodes, override the traverse function, since
  /// we need both pre- and post order traversal
  bool TraverseTranslationUnitDecl(TranslationUnitDecl *TU) {
    if (!TU)
      return true;

    Inherited::WalkUpFromTranslationUnitDecl(TU);

    // Do recursion on our own, since we want to exclude some children
    const auto DC = cast<DeclContext>(TU);
    for (auto *Child : DC->noload_decls()) {
      if (isa<TypedefDecl>(Child) || isa<RecordDecl>(Child) || isa<EnumDecl>(Child))
        continue;

      // Extern variable definitions at the top-level
      if (const auto VD = dyn_cast<VarDecl>(Child)) {
        if (VD->hasExternalStorage()) {
          continue;
        }
      }

      if (const auto FD = dyn_cast<FunctionDecl>(Child)) {
        // We try to avoid hashing of declarations that have no definition
        if (!FD->isThisDeclarationADefinition()) {
          bool doHashing = false;
          // HOWEVER! If this declaration is an alias Declaration, we
          // hash it no matter what
          if (FD->hasAttrs()) {
            for (const Attr *const A : FD->getAttrs()) {
              if (A->getKind() == attr::Kind::Alias) {
                doHashing = true;
                break;
              }
            }
          }
          if (!doHashing)
            continue;
        }
      }
      TraverseDecl(Child);
    }

    dumpRanges();
    return true;
  }

  std::set<void *> Visited;

  bool TraverseDecl(Decl *D) {
    if (!D)
      return true;

    auto Found = (Visited.find((void *)D) != Visited.end());
    if (Found)
      return true;
    Visited.insert((void *)D);

    if (isa<FunctionDecl>(D) || (isa<VarDecl>(D) && cast<VarDecl>(D)->hasGlobalStorage()) || (isa<RecordDecl>(D)) ||
        (isa<EnumDecl>(D)) || (isa<TypedefDecl>(D))) {
      // D->dump();
      PrintSourceRange("+", D->getSourceRange());
    }

    // Capture all Forward Declarations
    Decl *prev = D->getPreviousDecl();
    if (prev)
      TraverseDecl(prev);

    return Inherited::TraverseDecl(D);
  }

  /// When doing a semantic hash, we have to use cross-tree links to
  /// other parts of the AST, here we establish these links
#define DEF_GOTO_DECL(CLASS, EXPR)                                                                                     \
  bool Visit##CLASS(CLASS *O) {                                                                                        \
    Inherited::Visit##CLASS(O);                                                                                        \
    return TraverseDecl(EXPR);                                                                                         \
  }

  DEF_GOTO_DECL(DeclRefExpr, O->getDecl());
  DEF_GOTO_DECL(CallExpr, O->getCalleeDecl());
  DEF_GOTO_DECL(TypedefType, O->getDecl());
  DEF_GOTO_DECL(RecordType, O->getDecl());
  DEF_GOTO_DECL(EnumConstantDecl, dyn_cast_or_null<EnumDecl>(O->getDeclContext()));

  // The EnumType forwards to the declaration. The declaration does
  // not hand back to the type.
  DEF_GOTO_DECL(EnumType, O->getDecl());
  bool TraverseEnumDecl(EnumDecl *E) {
    /* In the original RecursiveASTVisitor
       > if (D->getTypeForDecl()) {
       >    TRY_TO(TraverseType(QualType(D->getTypeForDecl(), 0)));
       > }
       => NO, NO, NO, to avoid endless recursion
    */
    return Inherited::WalkUpFromEnumDecl(E);
  }

#define DEF_GOTO_TYPE(CLASS, EXPR)                                                                                     \
  bool Visit##CLASS(CLASS *O) {                                                                                        \
    Inherited::Visit##CLASS(O);                                                                                        \
    return TraverseType(EXPR);                                                                                         \
  }
  DEF_GOTO_TYPE(TypedefNameDecl, O->getUnderlyingType());
  DEF_GOTO_TYPE(ValueDecl, O->getType());

  bool VisitExpr(Expr *E) {
    if (!E)
      return true;
    Inherited::VisitExpr(E);
    // Print Expr Range in case the range stems from a macro
    // auto Range = E->getSourceRange();
    // PrintMacroExpansions(Range.getBegin());
    // Cross-Ref to all Types
    TraverseType(E->getType());
    return true;
  }

private:
  const ASTContext *Context;
  const SourceManager &SM;
  const CompilerInstance &CI;

  llvm::SetVector<Stmt *> SkippedStmts;

  llvm::DenseMap<FileID, std::vector<SourceRange>> UsedRanges;
  llvm::DenseMap<FileID, std::vector<SourceRange>> SkippedRanges;

  void printFileAndLine(SourceManager &SM, SourceLocation Loc) {
    PresumedLoc PLoc = SM.getPresumedLoc(Loc);
    if (PLoc.isValid()) {
      llvm::errs() << PLoc.getFilename() << ":" << PLoc.getLine() << ":" << PLoc.getColumn() << "\n";
    }
  }

  inline bool isExternalFile(SourceLocation Loc) {
    return SM.isInSystemHeader(Loc) || SM.isWrittenInBuiltinFile(Loc) || SM.isWrittenInCommandLineFile(Loc);
  }

  void PrintSourceRangeHelper(const SourceManager &SM, std::string tag, SourceRange range) {
    FullSourceLoc begin = Context->getFullLoc(range.getBegin());
    FullSourceLoc end = Context->getFullLoc(range.getEnd());
    auto File = begin.getFileEntry();
    auto FileEnd = end.getFileEntry();
    if (File == nullptr) {
      File = FileEnd;
    }
    if (!File)
      return;

    assert(SM.getFileID(range.getBegin()) == SM.getFileID(range.getEnd()));
    const FileID FID = SM.getFileID(range.getBegin());

    if (isExternalFile(range.getBegin()) && isExternalFile(range.getEnd())) {
      return;
    }

    switch (tag[0]) {
    case '+':
      UsedRanges[FID].emplace_back(range);
      break;
    // case '-':
    //   SkippedRanges.push_back(range);
    //   break;
    // default:
    //   llvm::errs() << "\n"; // This fixes the bug, I do not know why. `\n` does not work
    //   break;
    }
  }

  SourceLocation getEndOfLine(const SourceManager &SM, SourceLocation Loc) {
    std::pair<FileID, unsigned> LocInfo = SM.getDecomposedLoc(Loc);
    bool Invalid = false;
    StringRef File = SM.getBufferData(LocInfo.first, &Invalid);
    if (Invalid)
      return SourceLocation();

    const char *TokPtr = File.data() + LocInfo.second;
    while (*TokPtr != '\n' && *TokPtr != '\r' && *TokPtr != '\0')
      ++TokPtr;

    return Loc.getLocWithOffset(TokPtr - (File.data() + LocInfo.second));
  }

  void PrintSourceRange(std::string tag, SourceRange range) {
    // Extend the Range to include the beginning and the end of the line

    PresumedLoc PLoc;
    auto B = SM.getExpansionLoc(range.getBegin());
    auto E = SM.getExpansionLoc(range.getEnd());
    PLoc = SM.getPresumedLoc(B);
    if (PLoc.isValid()) {
      B = B.getLocWithOffset(1 - PLoc.getColumn());
    }
    SourceLocation E_t = getEndOfLine(SM, E);
    if (E_t.isValid())
      E = E_t;

    auto R = SourceRange(B, E);
    PrintSourceRangeHelper(SM, tag + "R ", R);
    for (const auto &[ExpansionLoc, MacroRanges] : MEM) {
      // printFileAndLine(SM, ExpansionLoc);
      if (SM.isPointWithin(ExpansionLoc, R.getBegin(), R.getEnd().getLocWithOffset(1))) {
        for (auto &R : MacroRanges)
          PrintSourceRangeHelper(SM, tag + "M ", R);
      }
    }
  }

  void dumpRanges() {
    // llvm::errs() << SkippedRanges.size() << '\n';
    //
    const std::string InfoFile = CI.getFrontendOpts().OutputFile + std::string("-info");
    // const string InfoFile = (MainFilename + ".info").str();
    std::error_code str_err;
    llvm::raw_fd_ostream Stream(StringRef(InfoFile), str_err);
    if (str_err.value() != 0)
      llvm::errs() << str_err.message() << '\n';

    llvm::json::OStream W(Stream);

    const std::string PPID{std::to_string(getppid())};
    const std::string FilePath = "/proc/" + PPID + "/cmdline";
    std::ifstream CommandLine{FilePath};
    std::string largs;
    if (CommandLine.good()) {
      std::string Arg;
      do {
        getline(CommandLine, Arg, '\0');
        largs.append(Arg + ' ');
      } while (Arg.size());
    }

    const std::string args = largs.substr(0, largs.length() - 2);

    const FileID MainFileID = SM.getMainFileID();
    FileManager &FM = SM.getFileManager();
    // const StringRef MainFilename = SM.getFilename(SM.getComposedLoc(MainFileID, 0));
    // TODO: This is a very expensive operation, despite its results being cached, and should only be used when the
    // physical layout of the file system is required, which is (almost) never.
    const StringRef MainFilename = FM.getCanonicalName(SM.getFileEntryForID(MainFileID));

    W.object([&] {
      W.attribute("tu", MainFilename);
      W.attribute("args", args);
      W.attributeArray("files", [&] {
        for (const auto &entry : UsedRanges) {
          const FileID FID = entry.first;
          const std::vector<SourceRange> &Ranges = entry.second;

          // const FileEntry *FileEntry = SM.getFileEntryForID(FID);
          const StringRef Filename = FM.getCanonicalName(SM.getFileEntryForID(FID));
          const SourceLocation EndOfFile = SM.getLocForEndOfFile(FID);
          const unsigned int Lines = SM.getSpellingLineNumber(EndOfFile) - 1;

          W.object([&] {
            W.attribute("lines", Lines);
            W.attribute("path", Filename);
            W.attributeArray("skips", [&] {
              for (const auto &Range : Ranges) {
                // remove PP directives from skips
                const auto begin = SM.getSpellingLineNumber(Range.getBegin());
                const auto end = SM.getSpellingLineNumber(Range.getEnd());
                W.array([&] {
                  W.value(begin);
                  W.value(end);
                });
              }
            });
          });
        }
      });
    });
  }
};
#endif // MYRECURSIVEASTVISITOR_H

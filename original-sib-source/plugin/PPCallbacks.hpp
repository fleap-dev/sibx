#ifndef PPCALLBACKS_H
#define PPCALLBACKS_H

#include <llvm/ADT/DenseMap.h>

#include <clang/Basic/SourceManager.h>
#include <clang/Frontend/CompilerInstance.h>
#include <clang/Lex/PPCallbacks.h>

using namespace std;
using namespace clang;

class MyPPCallbacks : public PPCallbacks {
private:
#if __clang_major__ >= 17
  const optional<const std::string> Variant;
  const optional<const std::string> Commit;
#else
  const Optional<const std::string> Variant;
  const Optional<const std::string> Commit;
#endif

  const CompilerInstance &CI;
  const SourceManager &SM;
  llvm::DenseMap<FileID, std::vector<SourceRange>> R;

public:
#if __clang_major__ >= 17
  MyPPCallbacks(CompilerInstance &C, optional<const std::string> &Variant, optional<const std::string> &Commit)
#else
  MyPPCallbacks(CompilerInstance &C, Optional<const std::string> &Variant, Optional<const std::string> &Commit)
#endif
      : Variant(Variant), Commit(Commit), CI(C), SM(C.getSourceManager()) {
  }

  virtual void SourceRangeSkipped(SourceRange Range, SourceLocation EndifLoc);
  virtual void FileChanged(SourceLocation Loc, FileChangeReason Reason, SrcMgr::CharacteristicKind FileType,
                           FileID PrevFID = FileID());
  virtual void EndOfMainFile();
};

#endif // PPCALLBACKS_H

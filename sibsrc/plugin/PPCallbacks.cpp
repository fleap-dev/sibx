#include "PPCallbacks.hpp"

#include <clang/Basic/FileManager.h>
#include <llvm/Support/JSON.h>

#include <llvm/Support/raw_ostream.h>

#include <fstream>
#include <unistd.h>

using namespace std;
using namespace llvm;

void MyPPCallbacks::SourceRangeSkipped(SourceRange Range, SourceLocation EndifLoc) {
  const SourceLocation Loc = Range.getBegin();
  assert(SM.getFileID(Loc) == SM.getFileID(Range.getEnd()));

  if (SM.isInSystemHeader(Loc) || SM.isWrittenInBuiltinFile(Loc) || SM.isWrittenInCommandLineFile(Loc)) {
    return;
  }

  const FileID FID = SM.getFileID(Loc);
  R[FID].emplace_back(Range);
}

void MyPPCallbacks::FileChanged(SourceLocation Loc, FileChangeReason Reason, SrcMgr::CharacteristicKind FileType,
                                FileID PrevFID) {
  if (Reason != FileChangeReason::EnterFile) {
    return;
  }

  if (SM.isInSystemHeader(Loc) || SM.isWrittenInBuiltinFile(Loc) || SM.isWrittenInCommandLineFile(Loc)) {
    return;
  }

  const FileID FID = SM.getFileID(Loc);
  R[FID]; // populate entry without skips
}

void MyPPCallbacks::EndOfMainFile() {
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

  // Compute filename
  FileManager &FM = SM.getFileManager();
  // const StringRef MainFilename = SM.getFilename(SM.getComposedLoc(MainFileID, 0));
  // TODO: This is a very expensive operation, despite its results being cached, and should only be used when the
  // physical layout of the file system is required, which is (almost) never.
  const StringRef MainFilename = FM.getCanonicalName(SM.getFileEntryForID(MainFileID));
  // const FileEntry *MainFileEntry = SM.getFileEntryForID(MainFileID);
  // const StringRef path = FM.getCanonicalName(MainFileEntry);

  const string InfoFile = CI.getFrontendOpts().OutputFile + string("-info");
  // const string InfoFile = (MainFilename + ".info").str();
  error_code str_err;
  raw_fd_ostream Stream(StringRef(InfoFile), str_err);
  if (str_err.value() != 0)
    errs() << str_err.message() << '\n';

  json::OStream W(Stream);

  W.object([&] {
    W.attribute("tu", MainFilename);
    W.attribute("args", args);
    if (this->Commit.has_value()) {
      W.attribute("commit", this->Commit);
    }
    if (this->Variant.has_value()) {
      W.attribute("variant", this->Variant);
    }
    W.attributeArray("files", [&] {
      for (const auto &entry : R) {
        const FileID FID = entry.first;
        const vector<SourceRange> Ranges = entry.second;

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
              const auto begin = SM.getSpellingLineNumber(Range.getBegin()) + 1;
              const auto end = SM.getSpellingLineNumber(Range.getEnd()) - 1;
              if (begin <= end) {
                W.array([&] {
                  W.value(begin);
                  W.value(end);
                });
              }
            }
          });
        });
      }
    });
  });
}

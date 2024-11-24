#include <clang/Frontend/CompilerInstance.h>
#include <clang/Frontend/FrontendActions.h>
#include <clang/Frontend/FrontendPluginRegistry.h>

#include "PPCallbacks.hpp"
#include "plugin.hpp"

using namespace std;
using namespace clang;

#if __clang_major__ >= 17
MyASTConsumer::MyASTConsumer(CompilerInstance &CI, optional<const std::string> &Variant,
                             optional<const std::string> &Commit) {
#else
MyASTConsumer::MyASTConsumer(CompilerInstance &CI, Optional<const std::string> &Variant,
                             Optional<const std::string> &Commit) {
#endif
  CI.getPreprocessor().addPPCallbacks(std::make_unique<MyPPCallbacks>(CI, Variant, Commit));
}

std::unique_ptr<ASTConsumer> MyPluginASTAction::CreateASTConsumer(CompilerInstance &CI, StringRef InFile) {
  return std::make_unique<MyASTConsumer>(CI, this->Variant, this->Commit);
}

bool MyPluginASTAction::ParseArgs(const CompilerInstance &CI, const std::vector<std::string> &args) {
  const char commit_flag[] = "--commit=";
  const char variant_flag[] = "--variant=";

  for (const std::string &arg : args) {
    if (arg.rfind(commit_flag, 0) == 0) {
      const std::string commit(arg, strlen(commit_flag));
      this->Commit.emplace(arg, strlen(commit_flag));
    } else if (arg.rfind(variant_flag, 0) == 0) {
      const std::string variant(arg, strlen(variant_flag));
      this->Variant.emplace(arg, strlen(variant_flag));
    }
  }
  return true;
}

// Automatically run the plugin before the main AST action
PluginASTAction::ActionType MyPluginASTAction::getActionType() { return AddBeforeMainAction; }

static FrontendPluginRegistry::Add<MyPluginASTAction> X("my-plugin", "My Plugin");

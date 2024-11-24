#include "plugin.hpp"
#include <clang/Frontend/CompilerInstance.h>

using namespace clang;

std::unique_ptr<ASTConsumer> MyPluginASTAction::CreateASTConsumer(CompilerInstance &CI, StringRef InFile) {
  return std::make_unique<MyASTConsumer>(CI);
}

bool MyPluginASTAction::ParseArgs(const CompilerInstance &CI, const std::vector<std::string> &args) { return true; }

// Automatically run the plugin before the main AST action
PluginASTAction::ActionType MyPluginASTAction::getActionType() { return AddBeforeMainAction; }

#ifndef CONFIG_TOOL
static FrontendPluginRegistry::Add<MyPluginASTAction> X("my-plugin", "My Plugin");
#endif

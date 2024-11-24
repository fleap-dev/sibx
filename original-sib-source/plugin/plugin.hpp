#ifndef PLUGIN_H
#define PLUGIN_H

#include <clang/Frontend/FrontendActions.h>

using namespace std;
using namespace clang;

class MyASTConsumer : public ASTConsumer {
public:
#if __clang_major__ >= 17
  MyASTConsumer(CompilerInstance &CI, optional<const std::string> &Variant, optional<const std::string> &Commit);
#else
  MyASTConsumer(CompilerInstance &CI, Optional<const std::string> &Variant, Optional<const std::string> &Commit);
#endif
};

class MyPluginASTAction : public PluginASTAction {
private:
#if __clang_major__ >= 17
  optional<const std::string> Variant;
  optional<const std::string> Commit;
#else
  Optional<const std::string> Variant;
  Optional<const std::string> Commit;
#endif

public:
  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI, StringRef InFile) override;

  virtual bool ParseArgs(const CompilerInstance &CI, const std::vector<std::string> &args) override;

  // Automatically run the plugin before the main AST action
  PluginASTAction::ActionType getActionType() override;
};

#endif // PLUGIN_H

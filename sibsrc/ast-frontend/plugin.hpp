#ifndef PLUGIN_H
#define PLUGIN_H

#include "MyRecursiveASTVisitor.hpp"

#include <clang/Frontend/CompilerInstance.h>
#include <clang/Frontend/FrontendActions.h>
#include <clang/Frontend/FrontendPluginRegistry.h>
#include <clang/Lex/Preprocessor.h>
#include <map>

class MyASTConsumer : public ASTConsumer {
  MacroExpansionMap MEM;
  Preprocessor &PP;
  SourceManager &SM;
  MyRecursiveASTVisitor Visitor;

public:
  MyASTConsumer(const CompilerInstance &CI)
      : PP(CI.getPreprocessor()), SM(PP.getSourceManager()), Visitor(&CI.getASTContext(), MEM, CI) {
    // Make sure that the Preprocessor does not outlive the MacroExpansionContext.
    PP.addPPCallbacks(std::make_unique<MacroExpansionRecorder>(PP, SM, MEM));
  };

  virtual void HandleTranslationUnit(clang::ASTContext &Context) override {
    Visitor.TraverseTranslationUnitDecl(Context.getTranslationUnitDecl());
  }
};

class MyPluginASTAction : public PluginASTAction {
public:
  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI, StringRef InFile) override;

  virtual bool ParseArgs(const CompilerInstance &CI, const std::vector<std::string> &args) override;

  // Automatically run the plugin before the main AST action
  PluginASTAction::ActionType getActionType() override;
};

#endif // PLUGIN_H

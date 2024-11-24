use std::path::Path;
use std::path::PathBuf;

use serde::Deserialize;
use serde::Serialize;

use crate::helper::*;

// https://clang.llvm.org/docs/JSONCompilationDatabase.html

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq, Clone)]
pub struct CompileCommands {
    commands: Vec<CompileCommand>,
}

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq, Clone)]
struct CompileCommand {
    directory: PathBuf,
    file: PathBuf,
    command: Option<String>,
    arguments: Option<Vec<String>>,
    output: Option<String>,
}

impl CompileCommands {
    pub fn read<P: AsRef<Path>>(path: P) -> Result<String, std::io::Error> {
        let data = std::fs::read_to_string(path)?;
        let cmds = serde_json::from_str(&data)?;

        let mut commands = Self { commands: cmds };
        Ok(commands.hash())
    }

    pub fn hash(&mut self) -> String {
        self.commands
            .sort_by(|a, b| a.file.partial_cmp(&b.file).unwrap());

        let mut bytes = vec![];
        for commands in self.commands.iter() {
            bytes.extend_from_slice(serde_json::to_string(commands).unwrap().as_bytes());
        }

        let hash = hash_fn(&bytes);

        hash.to_string()
    }
}

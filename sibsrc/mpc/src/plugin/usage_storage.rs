use std::collections::hash_map::Entry;
use std::collections::HashMap;
use std::collections::HashSet;
use std::io;
use std::path::Path;
use std::path::PathBuf;

use log::debug;
use rayon::prelude::*;
use serde::Deserialize;
use serde::Serialize;

use super::Info;
use super::Interval;
use super::IntervalTree;
use crate::git::Change;
use crate::interval;
use crate::CompileCommands;

// TODO: rename "skips" and others
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct UsageStorage<const PARSES_USED_LINES: bool> {
    pub repo: PathBuf,
    pub used_lines: HashMap<PathBuf, IntervalTree>,
    pub commands: HashMap<String, Option<String>>, // Variant -> CompileCommands Hash
}

impl<const PARSES_USED_LINES: bool> UsageStorage<PARSES_USED_LINES> {
    pub fn from<P: AsRef<Path>>(
        repo: P,
        compile_commands_hash: Option<String>,
        variant: String,
    ) -> Result<Self, io::Error> {
        let infos: Vec<(PathBuf, Vec<Interval>)> = super::list_info_files(repo.as_ref())
            .par_iter()
            .map(|info_file| {
                let data = std::fs::read_to_string(info_file).unwrap();
                let info: Info = serde_json::from_str(&data).unwrap();

                info.files
                    .into_iter()
                    .map(|file| {
                        let mut skipped = file.skips;
                        skipped.sort_by_key(|i| i.begin);

                        let used_lines = if PARSES_USED_LINES {
                            skipped
                        } else {
                            interval::Interval::invert(&skipped, file.lines)
                        };
                        let used_lines = used_lines
                            .into_iter()
                            .map(|i| Interval {
                                start: i.begin,
                                stop: i.end + 1,
                                val: variant.clone(),
                            })
                            .collect();

                        (file.path, used_lines)
                    })
                    .collect::<Vec<_>>()
            })
            .flatten()
            .collect();

        let mut temp = HashMap::<PathBuf, Vec<Interval>>::new();
        for (file, used_lines) in infos {
            match temp.entry(file) {
                Entry::Occupied(mut entry) => {
                    entry.get_mut().extend(used_lines);
                }
                Entry::Vacant(entry) => {
                    entry.insert(used_lines);
                }
            };
        }

        let compact_data = temp
            .into_par_iter()
            .map(|(file, used_lines)| {
                let mut tree = IntervalTree::new(used_lines);
                tree.merge_overlaps();
                (file, tree)
            })
            .collect();

        Ok(Self {
            repo: repo.as_ref().to_owned(),
            used_lines: compact_data,
            commands: HashMap::from([(variant, compile_commands_hash)]),
        })
    }

    fn get_all_variants(&self) -> Vec<String> {
        self.commands.keys().cloned().collect()
    }

    pub fn is_using_lines(tree: &IntervalTree, lines: &Change) -> bool {
        match lines {
            Change::Partly(lines) => {
                for lines in lines {
                    if tree.find(lines.start, lines.stop).next().is_some() {
                        return true;
                    }
                }
                false
            }
            Change::Full => true,
        }
    }

    fn find_variants_for_commit(dir: &Path, commit: &str) -> UsageStorage<PARSES_USED_LINES> {
        let content = std::fs::read_to_string(dir.join(commit).with_extension("json")).unwrap();
        serde_json::from_str(&content).unwrap()
    }

    fn get_affected(
        storage: &UsageStorage<PARSES_USED_LINES>,
        compile_commands_map: Option<Vec<String>>,
        changes: &HashMap<PathBuf, Change>,
    ) -> Vec<String> {
        let changed_by_use = changes
            .iter()
            .filter_map(|(file, changed)| {
                if let Some(used) = storage.used_lines.get(file) {
                    let variants: HashSet<&String> = match changed {
                        Change::Partly(changed_lines) => changed_lines
                            .iter()
                            .flat_map(|interval| {
                                used.find(interval.start, interval.stop).map(|i| &i.val)
                            })
                            .collect(),
                        Change::Full => used.iter().map(|i| &i.val).collect(),
                    };
                    Some(variants)
                } else {
                    None
                }
            })
            .flatten();

        let set: HashSet<&String> = if let Some(compile_commands_map) = compile_commands_map {
            let variant_commands = compile_commands_map
                .into_iter()
                .map(|s| {
                    let (v, p) = s.split_once(':').unwrap();
                    (v.to_owned(), p.to_owned())
                })
                .collect::<HashMap<String, String>>();

            let changed_by_cc = storage
                .commands
                .iter()
                .filter_map(|(variant, old_commands)| {
                    if let Some(old_commands) = old_commands {
                        if let Some(new_commands_path) = variant_commands.get(variant.as_str()) {
                            let new_commands = CompileCommands::read(new_commands_path).unwrap();
                            if old_commands != &new_commands {
                                debug!("{old_commands:?} -> {new_commands:?}");
                                return Some(variant);
                            }
                        }
                    }
                    None
                });

            #[cfg(debug_assertions)]
            debug!(
                "Changed (CC): {CC:?}",
                CC = changed_by_cc.clone().collect::<HashSet<_>>()
            );

            changed_by_cc.chain(changed_by_use).collect()
        } else {
            changed_by_use.collect()
        };

        set.into_iter().cloned().collect()
    }

    pub fn find_affected_variants<P: AsRef<Path>>(
        dir: P,
        commit: &str,
        compile_commands_map: Option<Vec<String>>,
        changes: HashMap<PathBuf, Change>,
        alarm_list: Option<&Vec<PathBuf>>,
        filter_asm: bool,
    ) -> Result<Vec<String>, std::io::Error> {
        let storage = Self::find_variants_for_commit(dir.as_ref(), commit);

        if filter_asm {
            let asm_changed = changes.keys().any(|file| {
                if let Some(ext) = file.extension() {
                    let ext = ext.to_ascii_lowercase();
                    ext == "s" || ext == "asm"
                } else {
                    false
                }
            });
            if asm_changed {
                return Ok(storage.get_all_variants());
            }
        }

        if let Some(alarm_list) = alarm_list {
            let some_file_changed = alarm_list.iter().any(|file| {
                let file = if file.is_relative() {
                    storage.repo.join(file)
                } else {
                    file.to_path_buf()
                };
                changes.contains_key(&file)
            });

            if some_file_changed {
                return Ok(storage.get_all_variants());
            }
        }

        Ok(Self::get_affected(&storage, compile_commands_map, &changes))
    }

    // TODO: make faster
    fn merge_into(
        old: &mut UsageStorage<PARSES_USED_LINES>,
        new: &UsageStorage<PARSES_USED_LINES>,
    ) {
        assert!(new.commands.keys().len() == 1);
        let new_variant = new.commands.keys().next().unwrap();
        assert!(
            !old.commands.contains_key(new_variant),
            "{:?} -> {:?}",
            old.commands,
            new.commands
        );
        old.commands.extend(new.commands.clone());

        // maybe fold and reduce?
        for (npath, ntree) in &new.used_lines {
            match old.used_lines.entry(npath.to_path_buf()) {
                Entry::Occupied(mut entry) => {
                    // merge trees
                    let old_data = entry.get().clone();
                    let merged = old_data.into_iter().chain(ntree.clone()).collect();
                    let merged = IntervalTree::new(merged);
                    entry.insert(merged);
                }
                Entry::Vacant(entry) => {
                    entry.insert(ntree.clone());
                }
            }
        }
    }

    pub fn dump_to_dir_accu<P: AsRef<Path>>(
        &self,
        path: P,
        version: &str,
    ) -> Result<(), std::io::Error> {
        let filename = format!("{version}.json");
        let file_path = path.as_ref().join(filename);

        if file_path.exists() {
            let content = std::fs::read_to_string(&file_path).unwrap();
            let mut old = serde_json::from_str(&content).unwrap();

            UsageStorage::merge_into(&mut old, self);

            old.dump(file_path)
        } else {
            self.dump(file_path)
        }
    }

    pub fn dump<P: AsRef<Path>>(&self, path: P) -> Result<(), std::io::Error> {
        let serialized = if cfg!(debug_assertions) {
            serde_json::to_string_pretty(&self)?
        } else {
            serde_json::to_string(&self)?
        };

        std::fs::write(path, serialized)
    }
}

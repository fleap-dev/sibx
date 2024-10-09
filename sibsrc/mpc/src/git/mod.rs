use std::{
    collections::{hash_map::Entry, HashMap},
    path::{Path, PathBuf},
};

use git2::{DiffDelta, DiffHunk, DiffOptions, Repository};
use log::{debug, trace};

use crate::plugin::Interval;

pub use crate::git::file_hunks::Hunk;

mod file_hunks;

#[derive(Debug)]
pub enum Change {
    Partly(Vec<Interval>),
    Full,
}

fn file_cb(_diff: DiffDelta, _: f32) -> bool {
    true
}

// checks whether the hunk's preprocessor directives are balanced
fn check_hunk_balanced_directives(content: &str) -> bool {
    let mut num_opened_directives = 0;

    for line in content.lines() {
        let line = line.trim_start();
        let line = if line.starts_with('+') || line.starts_with('-') {
            line[1..].trim_start()
        } else {
            line
        };
        if line.starts_with("#ifdef") || line.starts_with("#ifndef") || line.starts_with("#if") {
            num_opened_directives += 1;
        } else if line.starts_with("#elif") || line.starts_with("#else") {
            if num_opened_directives <= 0 {
                return false;
            }
        } else if line.starts_with("#endif") {
            if num_opened_directives <= 0 {
                return false;
            }
            num_opened_directives -= 1;
        }
    }

    num_opened_directives == 0
}

pub fn analyze<P>(
    path: P,
    base_commit: Option<&str>,
) -> Result<HashMap<PathBuf, Change>, git2::Error>
where
    P: AsRef<Path>,
{
    let path = path.as_ref().canonicalize().unwrap();
    let repo = Repository::open(&path)?;

    let mut diff_options = DiffOptions::default();
    diff_options.context_lines(0);

    let diff = if let Some(hash) = base_commit {
        let oid = repo.revparse_single(hash)?.id();
        let commit = repo.find_commit(oid)?;
        repo.diff_tree_to_workdir_with_index(Some(&commit.tree()?), Some(&mut diff_options))?
    } else {
        repo.diff_index_to_workdir(None, Some(&mut diff_options))?
    };

    let binary_cb = None;
    let line_cb = None;

    // [OldPath : Hunks]
    let mut hunks: HashMap<PathBuf, Change> = HashMap::new();

    let mut hunk_cb = |diff: DiffDelta, hunk: DiffHunk| {
        let old_file = diff.old_file().path().unwrap();
        let new_file = diff.new_file().path().unwrap();

        debug_assert_eq!(old_file, new_file);
        let old_file = path.join(old_file);

        // println!("{:?} {:?}", old_file, new_file);
        // println!(
        //     "{}:{} -> {}:{}",
        //     hunk.old_start(),
        //     hunk.old_lines(),
        //     hunk.new_start(),
        //     hunk.new_lines()
        // );
        // let header = String::from_utf8_lossy(hunk.header());
        // println!("{header}");
        let hunk = Hunk::from(hunk);
        match hunks.entry(old_file) {
            Entry::Occupied(mut entry) => {
                match entry.get_mut() {
                    Change::Partly(vec) => vec.push(hunk.old_lines),
                    _ => panic!(),
                };
            }
            Entry::Vacant(entry) => {
                entry.insert(Change::Partly(vec![hunk.old_lines]));
            }
        };
        true
    };

    diff.foreach(&mut file_cb, binary_cb, Some(&mut hunk_cb), line_cb)?;

    for (i, diff_delta) in diff.deltas().enumerate() {
        let file = diff_delta.old_file().path().unwrap();
        let file = path.join(file);

        let mut patch = git2::Patch::from_diff(&diff, i).unwrap().unwrap();
        let binding = patch.to_buf().unwrap();
        let text_diff = binding.as_str().unwrap();

        let mut alarm = false;
        let mut rm_buf = String::new();
        let mut add_buf = String::new();
        let mut in_hunk = false;
        for line in text_diff.lines() {
            if line.starts_with("@@") {
                in_hunk = true;
                if !rm_buf.is_empty() {
                    if !check_hunk_balanced_directives(&rm_buf) {
                        trace!("!!!!ALARM!!!!!, breaking \n {}", rm_buf);
                        alarm = true;
                        break;
                    } else {
                        rm_buf.clear();
                    }
                }
                if !add_buf.is_empty() {
                    if !check_hunk_balanced_directives(&add_buf) {
                        trace!("!!!!ALARM!!!!!, breaking \n {}", add_buf);
                        alarm = true;
                        break;
                    } else {
                        add_buf.clear();
                    }
                }
            } else if in_hunk {
                let buf = if line.starts_with('+') {
                    &mut add_buf
                } else {
                    &mut rm_buf
                };
                buf.push_str(line);
                buf.push('\n');
            }
        }
        if !alarm && !check_hunk_balanced_directives(&rm_buf) {
            trace!("!!!!ALARM!!!!! {}", rm_buf);
            alarm = true;
        } else if !alarm && !check_hunk_balanced_directives(&add_buf) {
            trace!("!!!!ALARM!!!!! {}", add_buf);
            alarm = true;
        }

        if alarm {
            debug!("Found imbalanced directives in {}", file.display());
            hunks.insert(file, Change::Full);
        }
    }

    Ok(hunks)
}

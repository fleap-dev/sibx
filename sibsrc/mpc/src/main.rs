use std::collections::HashMap;
use std::path::Path;
use std::path::PathBuf;
use std::process::ExitCode;
use std::time::Instant;

use clap::{Parser, Subcommand};
use git::Change;
use log::{debug, info, trace, LevelFilter};
use rayon::prelude::*;
use simple_logger::SimpleLogger;

use crate::checkpoint::Checkpoint;
use crate::plugin::CompileCommands;
use crate::plugin::UsageStorage;

mod checkpoint;
mod git;
mod helper;
mod interval;
mod plugin;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[command(subcommand)]
    command: Commands,
}

#[derive(clap::Args, Debug)]
struct DebugArgs {
    #[arg(short, long)]
    storage: PathBuf,

    #[arg(short, long)]
    commit: String,

    #[arg(short, long)]
    line: String,
}

#[derive(clap::Args, Debug)]
struct AnalyzeArgs {
    #[arg(short, long)]
    commit: Option<String>,

    #[arg(short, long)]
    variant: Option<String>,

    #[arg(short, long)]
    storage: Option<String>,

    #[arg(long, action, requires = "storage")]
    check_storage: bool,

    #[arg(long, action, requires = "storage")]
    dump: bool,

    #[arg(long, action, requires = "storage")]
    dump_only: bool,

    #[arg(long, action, requires = "storage")]
    compile_commands: bool,

    #[arg(long, default_value_t = String::from("compile_commands.json"))]
    compile_commands_path: String,

    #[arg(long, action = clap::ArgAction::Append, num_args = 1..)]
    compile_commands_path_map: Option<Vec<String>>,

    /// Files not allowed to change
    #[arg(long, action = clap::ArgAction::Append, num_args = 1..)]
    compare_git: Option<Vec<PathBuf>>,

    #[arg(long, action)]
    compare_checkpoints: bool,

    #[arg(long, action)]
    filter_asm: bool,

    dir: PathBuf,
}

#[derive(clap::Args, Debug)]
pub struct CheckpointArgs {
    #[arg(short, long)]
    storage: PathBuf,

    #[arg(short, long)]
    commit: Option<String>,

    #[arg(short, long)]
    variant: Option<String>,

    #[arg(short, long)]
    file: Vec<PathBuf>,

    dir: PathBuf,
}

#[derive(Subcommand, Debug)]
enum Commands {
    Debug(DebugArgs),
    Analyze(AnalyzeArgs),
    Checkpoint(CheckpointArgs),
}

const PARSE_USED_LINES: bool = false;

fn test_for_usage(args: &DebugArgs) -> Result<(), std::io::Error> {
    let (file, lines) = args.line.rsplit_once(':').map_or(
        (
            args.line.as_str(),
            crate::plugin::Interval {
                start: 0,
                stop: u32::MAX,
                val: String::new(),
            },
        ),
        |(file, line)| {
            let line = line.parse().unwrap();
            let interval = crate::plugin::Interval {
                start: line,
                stop: line + 1,
                val: String::new(),
            };
            (file, interval)
        },
    );

    let file = PathBuf::from(file);
    let mut file_lines = HashMap::new();
    file_lines.insert(file, Change::Partly(vec![lines]));

    let variants = UsageStorage::<PARSE_USED_LINES>::find_affected_variants(
        &args.storage,
        &args.commit,
        None,
        file_lines,
        None,
        false,
    )
    .unwrap();

    for variant in variants {
        println!("{variant}");
    }
    Ok(())
}

fn analyze(args: &AnalyzeArgs) -> Result<ExitCode, std::io::Error> {
    let mut exit_code = ExitCode::SUCCESS;
    let path = args.dir.canonicalize().unwrap();

    let compile_commands = if args.compile_commands {
        let p = Path::new(&args.compile_commands_path);
        let cc_path = if p.is_relative() {
            path.join(p)
        } else {
            p.to_path_buf()
        };

        Some(CompileCommands::read(cc_path)?)
    } else {
        None
    };

    let mut hunks = None;
    if !args.dump_only {
        info!("Loading git information...");
        let now = Instant::now();
        hunks = Some(git::analyze(&path, args.commit.as_deref()).unwrap());
        info!("Completed in {:?}", Instant::now().duration_since(now));
        // dbg!(&hunks);
    }

    if !args.check_storage || args.dump || args.dump_only {
        info!("Loading build information...");
        let now = Instant::now();
        let storage = UsageStorage::<PARSE_USED_LINES>::from(
            &path,
            compile_commands.clone(),
            args.variant.clone().unwrap_or_default(),
        )
        .unwrap();
        info!("Completed in {:?}", Instant::now().duration_since(now));

        // dbg!(&storage.data);
        if !args.check_storage && !args.dump_only {
            let hunks = hunks.as_ref().unwrap();
            info!("Analyzing impact...");
            let now = Instant::now();

            let mut found = false;
            if args.filter_asm {
                let asm_changed = hunks.keys().any(|file| {
                    if let Some(ext) = file.extension() {
                        let ext = ext.to_ascii_lowercase();
                        ext == "s" || ext == "asm"
                    } else {
                        false
                    }
                });
                if asm_changed {
                    found = true;
                }
            }

            if !found {
                if let Some(alarm_list) = &args.compare_git {
                    let some_file_changed = alarm_list.iter().any(|file| {
                        let file = if file.is_relative() {
                            path.join(file)
                        } else {
                            file.to_path_buf()
                        };
                        if hunks.contains_key(&file) {
                            info!("Some change in {:?}", file);
                            true
                        } else {
                            false
                        }
                    });

                    if some_file_changed {
                        found = true;
                    }
                }
            }

            if !found
                && args.compare_checkpoints
                && !Checkpoint::find_affected_variants(
                    &args.dir,
                    args.commit.as_deref().unwrap_or("unknown"),
                )?
                .is_empty()
            {
                found = true;
            }

            if !found {
                found = storage.used_lines.par_iter().any(|(file, uses)| {
                    trace!("Analyzing {:?}", file);

                    if let Some(hunks) = hunks.get(file) {
                        if UsageStorage::<PARSE_USED_LINES>::is_using_lines(uses, hunks) {
                            info!("Relevant change in {:?}", file);
                            return true;
                        }
                    }

                    false
                });
            }
            if found {
                exit_code = ExitCode::from(1);
            }
            info!("Completed in {:?}", Instant::now().duration_since(now));
        }

        if args.dump || args.dump_only {
            info!("Dumping data...");
            let now = Instant::now();

            storage.dump_to_dir_accu(
                args.storage.as_ref().unwrap(),
                args.commit.as_deref().unwrap_or("unknown"),
            )?;

            info!("Completed in {:?}", Instant::now().duration_since(now));
        }
    }

    if args.check_storage && !args.dump_only {
        let hunks = hunks.unwrap();
        info!("Analyzing impact...");
        let now = Instant::now();
        let mut variants = UsageStorage::<PARSE_USED_LINES>::find_affected_variants(
            args.storage.as_ref().unwrap(),
            args.commit.as_ref().unwrap(),
            args.compile_commands_path_map.clone(),
            hunks,
            args.compare_git.as_ref(),
            args.filter_asm,
        )?;

        if args.compare_checkpoints {
            let mut additional_variants = Checkpoint::find_affected_variants(
                &args.dir,
                args.commit.as_deref().unwrap_or("unknown"),
            )?;
            debug!("Affected variants by hash: {additional_variants:?}");
            variants.append(&mut additional_variants);
        }
        info!("Completed in {:?}", Instant::now().duration_since(now));
        info!("{variants:?} affected");
    }

    Ok(exit_code)
}

fn main() -> Result<ExitCode, std::io::Error> {
    SimpleLogger::new()
        .with_level(LevelFilter::Debug)
        .init()
        .unwrap();

    let args = Args::parse();

    let result = match &args.command {
        Commands::Debug(args) => test_for_usage(args).map(|_| ExitCode::SUCCESS),
        Commands::Analyze(args) => analyze(args),
        Commands::Checkpoint(args) => Checkpoint::create(args).map(|_| ExitCode::SUCCESS),
    };

    result.unwrap();

    Ok(ExitCode::SUCCESS)
}

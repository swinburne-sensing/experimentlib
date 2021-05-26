import subprocess


class GitError(Exception):
    pass


class CommandNotFound(GitError):
    pass


class CommandError(GitError):
    pass


# From http://stackoverflow.com/questions/12826723/possible-to-extract-the-git-repo-revision-hash-via-python-code
def get_git_hash() -> str:
    try:
        git_process = subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as ex:
        raise CommandNotFound('git binary not accessible')

    # Read output from process
    (git_process_out, git_process_err) = git_process.communicate()

    # Decode output
    git_process_out = git_process_out.decode().strip()
    git_process_err = git_process_err.decode().strip()

    if len(git_process_err) > 0:
        raise CommandError(f"git binary returned error while reading hash: \"{git_process_err}\"")

    return git_process_out

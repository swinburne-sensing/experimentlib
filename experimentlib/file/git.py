import inspect
import os.path
import subprocess
import typing


class CommandNotFound(FileNotFoundError):
    pass


class GitError(Exception):
    pass


def get_git_hash(path: typing.Optional[str] = None, length: typing.Optional[int] = None) -> str:
    """ Fetch the current git commit hash of the specified director, optionally truncating the hash to a shorted format.

        Inspired by: https://stackoverflow.com/questions/12826723/possible-to-extract-the-git-repo-revision-hash-via-python-code

        :param path: path of git repository, defaults to callers module file path
        :param length: optionally truncate hash to specified length
        :return: hash as a str
        """
    if path is None:
        # Get caller from stack and
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])

        path, _ = os.path.split(module.__file__)

    try:
        git_process = subprocess.Popen(['git', 'rev-parse', 'HEAD'], cwd=path, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise CommandNotFound('git binary not accessible')

    # Read output from process
    (git_process_out, git_process_err) = git_process.communicate()

    # Decode output
    git_process_out = git_process_out.decode().strip()
    git_process_err = git_process_err.decode().strip()

    if len(git_process_err) > 0:
        raise GitError(f"git binary returned error while reading hash: \"{git_process_err}\"")

    if length:
        return git_process_out[:length]
    else:
        return git_process_out

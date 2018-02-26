# Contributing to Meditor

We'd love for you to contribute to our source code and to make Meditor better!
Here are the guidelines we'd like you to follow:

* [Code of Conduct](#coc)
* [Questions and Problems](#question)
* [Quality Models](#qualitymodel)
* [Issues and Bugs](#issue)
* [Feature Requests](#feature)
* [Issue Submission Guidelines](#submit)
* [Pull Request Submission Guidelines](#submit-pr)
* [Signing the CLA](#cla)

## <a name="coc"></a> Code of Conduct

Help us keep Meditor open and inclusive. Please read and follow our [Code of Conduct][coc].

## <a name="requests"></a> Questions, Bugs, Features

### <a name="question"></a> Got a Question or Problem?

Meditor is yet a small project so just use GitHub issues for sending your question.

### <a name="qualitymodel"></a> Do you want to contribute a Quality Model?

Just follow the same procedure than [sending a new feature](#feature).

### <a name="issue"></a> Found an Issue or Bug?

If you find a bug in the source code, you can help us by submitting an issue to our
[GitHub Repository][github]. Even better, you can submit a Pull Request with a fix.

**Please see the [Submission Guidelines](#submit) below.**


### <a name="feature"></a> Missing a Feature?

You can request a new feature by submitting an issue to our [GitHub Repository][github-issues].

If you would like to implement a new feature then consider what kind of change it is:

* **Major Changes** that you wish to contribute to the project should be discussed first in an
  [GitHub issue][github-issues] that clearly outlines the changes and benefits of the feature.
* **Small Changes** can directly be crafted and submitted to the [GitHub Repository][github]
  as a Pull Request. See the section about [Pull Request Submission Guidelines](#submit-pr).


## <a name="submit"></a> Issue Submission Guidelines
Before you submit your issue search the archive, maybe your question was already answered.

If your issue appears to be a bug, and hasn't been reported, open a new issue. Help us to maximize
the effort we can spend fixing issues and adding new features, by not reporting duplicate issues.

The "[new issue][github-new-issue]" form contains a number of prompts that you should fill out to
make it easier to understand and categorize the issue.

In general, providing the following information will increase the chances of your issue being dealt
with quickly:

* **Overview of the Issue** - if an error is being thrown a non-minified stack trace helps
* **Motivation for or Use Case** - explain why this is a bug for you
* **Meditor Version(s)** - is it a regression?
* **Browsers and Operating System** - is this a problem with all browsers or only specific ones?
* **Reproduce the Error** - provide an unambiguous set of stepsto reproduce the error.
* **Related Issues** - has a similar issue been reported before?
* **Suggest a Fix** - if you can't fix the bug yourself, perhaps you can point to what might be
  causing the problem (line of code or commit)

**If you get help, help others. Good karma rulez!**

## <a name="submit-pr"></a> Pull Request Submission Guidelines
Before you submit your pull request consider the following guidelines:

* Search [GitHub](https://github.com/Bitergia/meditor/pulls) for an open or closed Pull Request
  that relates to your submission. You don't want to duplicate effort.
* Close [meditor][github] Django app
* Make your changes in a new git branch:

    ```shell
    git checkout -b my-fix-branch master
    ```

* Create your patch commit, including appropriate test cases.
* Run `flake8` to check that you have followed the automatically enforced coding rules
* Commit your changes using a descriptive commit message with a first line with the subject/summary of the commit, and the rest of the lines describing what the commit does.

    ```shell
    git commit -a
    ```
  Note: the optional commit `-a` command line option will automatically "add" and "rm" edited files.

* Push your branch to GitHub:

    ```shell
    git push origin my-fix-branch
    ```

* In GitHub, send a pull request to `meditor:master`. This will trigger the Travis integration.

* If you find that the Travis integration has failed, look into the logs on Travis to find out
if your changes caused test failures, the commit message was malformed etc. If you find that the
tests failed or times out for unrelated reasons, you can ping a team member so that the build can be
restarted.

* If we suggest changes, then:

  * Make the required updates.
  * Commit your changes to your branch (e.g. `my-fix-branch`).
  * Push the changes to your GitHub repository (this will update your Pull Request).

    You can also amend the initial commits and force push them to the branch.

    ```shell
    git rebase master -i
    git push origin my-fix-branch -f
    ```

    This is generally easier to follow, but seperate commits are useful if the Pull Request contains
    iterations that might be interesting to see side-by-side.

That's it! Thank you for your contribution!

#### After your pull request is merged

After your pull request is merged, you can safely delete your branch and pull the changes
from the main (upstream) repository:

* Delete the remote branch on GitHub either through the GitHub web UI or your local shell as follows:

    ```shell
    git push origin --delete my-fix-branch
    ```

* Check out the master branch:

    ```shell
    git checkout master -f
    ```

* Delete the local branch:

    ```shell
    git branch -D my-fix-branch
    ```

* Update your master with the latest upstream version:

    ```shell
    git pull --ff upstream master
    ```


Thanks to AngularJS for its great [CONTRIBUTING.md][angular-contrib] in which is based this one.

[angular-contrib]: https://github\.com/Bitergia/meditor/blob/master/CONTRIBUTING.md
[coc]: https://github\.com/Bitergia/meditor/blob/master/CODE_OF_CONDUCT.md
[github-issues]: https://github\.com/Bitergia/meditor/issues
[github-new-issue]: https://github\.com/Bitergia/meditor/issues/new
[github]: https://github\.com/Bitergia/meditor

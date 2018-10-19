# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a 
   build.
2. This project uses flake8 to conform with common Python standards. Makse sure
   to run your code through linter using latest version of flake8, before pull request.
3. Bad documnentation is a Bug. If your change demands documentation update, please do so. If you
   find an issue with documentation, take the time to improve or fix it.
4. pytest is used for automated testing. Please make sure to update tests are needed, and to run
   `make test`, before submitting your pull request. This should prevent issues with TravisCI and
   make the review and merging process easier and faster.
5. Update the README.md with details of changes to the interface, this includes new environment 
   variables, exposed ports, useful file locations and container parameters.
6. Increase the version numbers in any examples files and the README.md to the new version that this
   Pull Request would represent. The versioning scheme we use is [SemVer](http://semver.org/).
7. You may merge the Pull Request in once you have the sign-off of one other developer. If you 
   do not have permission to do that, you may request reviewer to merge it for you.

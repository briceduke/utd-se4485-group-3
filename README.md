# SE4485 Software Engineering Project - Group 3

Below is a list of resources for working on this project:

### Upcoming Due Dates:

**Project Management Plan - Due 09/12/25 11:59PM**
 - Status: Reviewed by sponsor and submitted.

**Requirements Documentation - Due 09/26/25 11:59PM**
 - Status: Reviewed by sponsor and submitted.

**Architecture Documentation - Due 10/24/25 11:59PM**
 - Status: Reviewed by sponsor and submitted.

**Detailed Design Documentation - Due 11/07/25 11:59PM**
 - Status: In progress.

### Google Docs Links

You must request access to view these documents

1. [Project Management Plan](https://docs.google.com/document/d/1FfJ6ZJQwvdmUM3KI6IC-4oyhLll8w04LknVZpzxnneo/edit?usp=sharing)
2. [Requirements Documentation](https://docs.google.com/document/d/1K-C-Qxv-ak3iMfZVtWAqiY6MwcaQ7BcablQzacZmCMs/edit?usp=sharing)
3. [Architecture Documentation](https://docs.google.com/document/d/11jxPOv6BJXbTQbjQYScvk9rQOuxu6_rMCpXJJGDyp3c/edit?usp=sharing)
4. [Detailed Design Documentation](https://docs.google.com/document/d/18Rr_8qcgyI2ZGt3-YASBVLLZP__4tgzuK9ln_h2fPpA/edit?usp=sharing)

### Configuration Management Guidelines

Pursuant to the class's document on [using CM tools](https://course.techconf.org/se4485/Template/CM-Tool.pdf), we must document our changes when writing code or supplemental documents.

**For editing docs**

1. Name the change in the version history tab in google docs
2. add a comment to your changes noting what has changed
3. get two other members to reply to your comments with a review

![google docs version history location](https://github.com/user-attachments/assets/a6140abb-7027-4c19-b8da-c24f46b2032c)

When pushing major changes of the docs to GitHub:

1. Compile all comments added to the Google doc since the last GitHub push and add them as a changelog to the PR
2. Get two reviewers for the PR

Once the changes have been pushed to the GitHub, clear all Google doc comments

**For editing code**

1. Create a new branch for the changes
2. Make the changes
3. Push the changes to the branch
4. Create a PR
5. Get two reviewers for the PR
6. Merge the PR into main
7. Delete the branch

### Development Setup

1. Install the development dependencies, virtual environment, and build the utilities
`make dev-install`
2. Run the utilities
`make run-dl` or `make run-dp`

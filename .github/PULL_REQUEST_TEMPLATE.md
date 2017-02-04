### PR guidelines

#### PR comment
- Description
  - Please provide an elaborate description of the problem you are trying to solve.
- Design notes
  - If this is a new feature, please provide design notes on the change which the next developer looking at the code might want to know upfront.
- Side effects
  - Are you aware of any OS-specific deviations, side effects, unhandled scenarios etc.? Let us know.
- Test cases
  - Which scenarios have you tested already? A list of commands are welcome.

#### Program help
This is more important than your design or code! Users check this first.
- README.md
  - New dependencies? Update them under **Installation**.
  - New program option? Update program help under **Cmdline options** verbatim. The short description in help should be more or less aligned to other option descriptions.
  - Add an example, if required under **Examples**.
  - Update **Operational notes** if your change affects current behaviour, links to environment variables etc.
- Man page
  - Update program options.
  - Add the same example, if you ave added one in README.md.
  - Update **Operational notes**. However, new environment variables go under **ENVIRONMENT** section.
- Completion scripts
  - Add new program options to completion scripts for bash, fish and zsh.

#### Coding guidelines
- Add new program options to a reasonable group.
- *Single quote, single quote, single all the way!*
- A single line should be less than 80 chars in length.
- No trailing whitespaces.
- Add new API documentation, reasonable code comments.
- If possible, add test cases for your new API under `tests/`. We are Travis integrated.
- If possible, squash everything to a single commit.

--- PLEASE DELETE THIS LINE AND EVERYTHING ABOVE ---

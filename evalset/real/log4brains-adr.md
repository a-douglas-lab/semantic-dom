# Log4brains Architecture Decision Records

## Use Markdown Architectural Decision Records

- Status: accepted
- Date: 2020-09-24

### Context and Problem Statement

We want to record architectural decisions made in this project. Which format and structure should these records follow?

### Considered Options

- [MADR](https://adr.github.io/madr/) 2.1.2 with Log4brains patch
- [MADR](https://adr.github.io/madr/) 2.1.2 – The original Markdown Architectural Decision Records
- [Michael Nygard's template](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions) – The first incarnation of the term "ADR"
- [Sustainable Architectural Decisions](https://www.infoq.com/articles/sustainable-architectural-design-decisions) – The Y-Statements
- Other templates listed at <https://github.com/joelparkerhenderson/architecture_decision_record>
- Formless – No conventions for file format and structure

### Decision Outcome

Chosen option: "MADR 2.1.2 with Log4brains patch", because

- Implicit assumptions should be made explicit. Design documentation is important to enable people understanding the decisions later on. See also [A rational design process: How and why to fake it](https://doi.org/10.1109/TSE.1986.6312940).
- The MADR format is lean and fits our development style.
- The MADR structure is comprehensible and facilitates usage & maintenance.
- The MADR project is vivid.
- Version 2.1.2 is the latest one available when starting to document ADRs.
- The Log4brains patch adds more features, like tags.

The "Log4brains patch" performs the following modifications to the original template:

- Change the ADR filenames format (`NNN-adr-name` becomes `YYYYMMDD-adr-name`), to avoid conflicts during Git merges.
- Add a `draft` status, to enable collaborative writing.
- Add a `Tags` field.

## Multi-packages architecture in a monorepo with Yarn and Lerna

- Status: accepted
- Date: 2020-09-25

### Context and Problem Statement

We have to define the initial overall architecture of the project. For now, we are sure that we want to provide these features:

- Local preview web UI
- Static Site Generation from the CI/CD
- CLI to create a new ADR quickly

In the future, we might want to provide these features:

- Create/edit ADRs from the local web UI
- VSCode extension to create and maybe edit an ADR from the IDE
- Support ADR aggregation from multiple repositories

### Considered Options

- Monolith
- Multi-packages, multirepo
- Multi-packages, monorepo
- with NPM and scripts for links and publication
- with Yarn and scripts for publication
- with Yarn and Lerna

### Decision Outcome

Chosen option: "Multi-packages, monorepo, with Yarn and Lerna", because

- We don't want a monolith because we want the core library/API to be very well tested and probably developed with DDD and hexagonal architecture. The other packages will just call this core API, they will contain fewer business rules as possible. As we are not so sure about the features we will provide in the future, this is good for extensibility.
- Yarn + Lerna seems to be a very good practice used by a lot of other open-source projects to publish npm packages.

### Links <!-- optional -->

- [A Beginner's Guide to Lerna with Yarn Workspaces](https://medium.com/@jsilvax/a-workflow-guide-for-lerna-with-yarn-workspaces-60f97481149d)
- [Step by Step Guide to create a Typescript Monorepo with Yarn Workspaces and Lerna](https://blog.usejournal.com/step-by-step-guide-to-create-a-typescript-monorepo-with-yarn-workspaces-and-lerna-a8ed530ecd6d)

## Use Prettier-ESLint Airbnb for the code style

- Status: accepted
- Date: 2020-09-25

### Context and Problem Statement

We have to choose our lint and format tools, and the code style to enforce as well.

### Considered Options

- Prettier only
- ESLint only
- ESLint with Airbnb code style
- ESLint with StandardJS code style
- ESLint with Google code style
- Prettier-ESLint with Airbnb code style
- Prettier-ESLint with StandardJS code style
- Prettier-ESLint with Google code style

### Decision Outcome

Chosen option: "Prettier-ESLint with Airbnb code style", because

- Airbnb code style is widely used (see [npm trends](https://www.npmtrends.com/eslint-config-airbnb-vs-eslint-config-google-vs-standard-vs-eslint-config-standard))
- Prettier-ESLint enforce some additional code style. We like it because the more opinionated the code style is, the less debates there will be :-)

In addition, we use also Prettier to format json and markdown files.

#### Positive Consequences <!-- optional -->

- Developers are encouraged to use the [Prettier ESLint](https://marketplace.visualstudio.com/items?itemName=rvest.vs-code-prettier-eslint) and [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) VSCode extensions while developing to auto-format the files on save
- And they are encouraged to use the [ESLint VS Code extension](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) as well to highlight linting issues while developing

## Use the ADR number as its unique ID

- Status: superseded by [20201016-use-the-adr-slug-as-its-unique-id](20201016-use-the-adr-slug-as-its-unique-id.md)
- Date: 2020-09-26

### Context and Problem Statement

We need to be able to identify uniquely an ADR, especially in these contexts:

- Web: to build its URL
- CLI: to identify an ADR in a command argument (example: "edit", or "preview")

### Considered Options

- ADR number (ie. filename prefixed number, example: `0001-use-markdown-architectural-decision-records.md`)
- ADR filename
- ADR title

### Decision Outcome

Chosen option: "ADR number", because

- It is possible to have duplicated titles
- The filename is too long to enter without autocompletion, but we could support it as a second possible identifier for the CLI in the future
- Other ADR tools like [adr-tools](https://github.com/npryce/adr-tools) already use the number as a unique ID

## Avoid default exports

- Status: accepted
- Date: 2020-09-27

### Decision

We will avoid default exports in all our codebase, and use named exports instead.

### Links

- <https://humanwhocodes.com/blog/2019/01/stop-using-default-exports-javascript-module/>
- <https://basarat.gitbook.io/typescript/main-1/defaultisbad>

## Use the ADR slug as its unique ID

- Status: accepted
- Date: 2020-10-16

### Context and Problem Statement

Currently, ADR files follow this format: `NNNN-adr-title.md`, with NNNN being an incremental number from `0000` to `9999`. It causes an issue during a `git merge` when two developers have created a new ADR on their respective branch. There is a conflict because [an ADR number must be unique](20200926-use-the-adr-number-as-its-unique-id.md).

### Decision

From now on, we won't use ADR numbers anymore. An ADR will be uniquely identified by its slug (ie. its filename without the extension), and its filename will have the following format: `YYYYMMDD-adr-title.md`, with `YYYYMMDD` being the date of creation of the file.

As a result, there won't have conflicts anymore and the files will still be correctly sorted in the IDE thanks to the date.

Finally, the ADRs will be sorted with these rules (ordered by priority):

- 1. By Date field, in the markdown file (if present)
- 2. By Git creation date (does not follow renames)
- 3. By file creation date if no versioned yet
- 4. By slug

The core library is responsible for sorting.

### Links

- Supersedes [20200926-use-the-adr-number-as-its-unique-id](20200926-use-the-adr-number-as-its-unique-id.md)

## The core API is responsible for enhancing the ADR markdown body with MDX

- Status: accepted
- Date: 2020-10-26

### Context and Problem Statement

The markdown body of ADRs cannot be used as is, because:

- Links between ADRs have to be replaced with correct URLs
- Header (status, date, deciders etc...) has to be rendered with specific components

### Decision Drivers <!-- optional -->

- Potential future development of a VSCode extension

### Considered Options

- Option 1: the UI is responsible
- Option 2: the core API is responsible (with MDX)

### Decision Outcome

Chosen option: "Option 2: the core API is responsible (with MDX)". Because if we develop the VSCode extension, it is better to add more business logic into the core package, and it is better tested.

#### Positive Consequences <!-- optional -->

- The metadata in the header is simply removed

#### Negative Consequences <!-- optional -->

- Each UI package will have to implement its own Header component

## Use Lunr for search

- Status: accepted
- Date: 2020-11-03

### Context and Problem Statement

We have to provide a search bar to perform full-text search on ADRs.

### Decision Drivers <!-- optional -->

- Works in preview mode AND in the statically built version
- Provides good fuzzy search and stemming capabilities
- Is fast enough to be able to show results while typing
- Does not consume too much CPU and RAM on the client-side, especially for the statically built version

### Considered Options

- Option 1: Fuse.js
- Option 2: Lunr.js

### Decision Outcome

Chosen option: "Option 2: Lunr.js".

### Pros and Cons of the Options <!-- optional -->

#### Option 1: Fuse.js

<https://fusejs.io/>

- Fast indexing
- Slow searching
- Only fuzzy search, no stemming

#### Option 2: Lunr.js

<https://lunrjs.com/>

- Slow indexing, but supports index serialization to pre-build them
- Fast searching
- Stemming, multi-language support
- Retrieves the position of the matched tokens

### Links

- <https://wiki.gpii.net/w/Technology_Evaluation_-_Static_Site_Search>

## Distribute Log4brains as a global NPM package

- Status: accepted
- Date: 2021-01-13

Technical Story: <https://github.com/thomvaill/log4brains/issues/14#issuecomment-750154907>

### Context and Problem Statement

Log4brains (`v1.0.0-beta.4`) installation procedure is currently optimized for JS projects and looks like this:

- Run `npx init-log4brains`
- Which installs locally `@log4brains/cli` and `@log4brains/web`
- And creates custom entries in `package.json`'s `scripts` section:
- `"log4brains-preview": "log4brains-web preview"`
- `"log4brains-build": "log4brains-web build"`
- `"adr": "log4brains adr"`

For non-JS projects, you have to install manually the packages and the `npx init-log4brains` script does not work.

Since Log4brains is intended for all projects, not especially JS ones, we have to make the installation procedure simpler and language-agnostic.

### Decision Drivers <!-- optional -->

- Simplicity of the installation procedure
- Language agnostic
- Initialization script works on any kind of project
- Faster "getting started"

### Decision Outcome

The new installation procedure is now language agnostic and will be the following:

Code: npm install -g log4brains ⏎ log4brains init

Log4brains will be distributed as a global NPM package named `log4brains`, which provides a global `log4brains` command.

- This global package will require the existing `@log4brains/cli` and `@log4brains/web` packages
- `init-log4brains` will be renamed to `@log4brains/init` and required as a dependency

#### Consequences

For a JS project, it is now impossible to pin Log4brains to a specific version. We may implement a [xojs/xo](https://github.com/xojs/xo)-like behavior later: "the CLI will use your local install of XO when available, even when run globally."

### Links

- [Related GitHub issue](https://github.com/thomvaill/log4brains/issues/14#issuecomment-750154907)

## Transition to Simplified Git Flow

- Status: superseded by [20241217-switch-back-to-github-flow](20241217-switch-back-to-github-flow.md)
- Date: 2024-09-26

### Context and Problem Statement

The existing GitHub Flow process lacked clarity for stable releases and was overly manual, making it hard to delegate and streamline contributions. The need was for a more structured yet simple workflow that would facilitate testing and contributions while automating releases.

Additional context in [Discussion #108: Does this project need a new maintainer?](https://github.com/thomvaill/log4brains/discussions/108)

### Decision Drivers

- Need for automation in releases.
- Be able to merge more quickly whithout breaking the stable branch, while making it possible for beta testers to test the new features.
- Easier delegation to new maintainers.
- Simplified yet structured process for contributors.
- Clearer separation between ongoing development and stable releases.

### Considered Options

- Continue with GitHub Flow.
- Transition to Simplified Git Flow.
- Full Git Flow with release branches.

### Decision Outcome

Chosen option: **Simplified Git Flow**, because it provides structure (separating development from stable releases) without excessive complexity. It also allows for automated canary/beta releases and easier delegation for merging feature branches to `develop`.

#### Positive Consequences

- Clear separation of development (`develop`) and stable (`stable`) branches.
- Automated beta releases from `develop` to facilitate early testing.
- Allows contributors to participate in testing beta features and reduces the manual overhead of testing and releasing stable versions
- Easier to delegate responsibilities (Canary vs. Core Maintainers, see [CONTRIBUTING.md](CONTRIBUTING.md)).
- More streamlined versioning via Conventional Commits.

#### Negative Consequences

- Contributors need to adjust to using `develop` for PRs instead of `stable`.
- Slight learning curve for Conventional Commits.

### Pros and Cons of the Options

#### Continue with GitHub Flow

- Good, because it’s simpler with fewer branches.
- Bad, because it lacks separation of development and stable code.
- Bad, because manual testing and release increase bottlenecks.

#### Simplified Git Flow

- Good, because it balances structure with simplicity.
- Good, because it allows easier delegation to maintainers.
- Bad, because it introduces a new `develop` branch, which may need adjustment for contributors.

#### Full Git Flow

- Good, because it provides a full release management process.
- Bad, because it adds unnecessary complexity for smaller open-source projects.

## Switch back to GitHub Flow, but keeping the automated beta releases

- Status: accepted
- Date: 2024-12-17

### Context and Problem Statement

The previous decision to adopt a Simplified Git Flow with a `develop` and `stable` branch aimed to provide clearer separation between development and releases while enabling automated beta releases. However, we faced tooling limitations.

Specifically, **Lerna**, which we use for managing our monorepo, does not integrate well with Git Flow processes ([Lerna issue #2023](https://github.com/lerna/lerna/issues/2023#issuecomment-480402592)), when managing both a `develop` and `stable` branches: we cannot make Lerna publish a stable release from a different branch than the main one.

### Decision Drivers <!-- optional -->

- Make Lerna work again for stable releases
- Keep the benefits of the previous workflow:
- Need for automation in releases.
- Be able to merge more quickly whithout breaking the stable branch, while making it possible for beta testers to test the new features.
- Easier delegation to new maintainers.
- Simplified yet structured process for contributors.
- Clearer separation between ongoing development and stable releases.

### Considered Options

- Option 1: Patch Lerna to keep the Simplified Git Flow (as described in the link above)
- Option 2: Switch back to Github Flow, but keeping the automated beta releases

### Decision Outcome

Chosen option: "Option 2: Switch back to Github Flow, but keeping the automated beta releases", because it fullfils all the requirements. In fact, we can still merge quickly pull requests without releasing a stable release, while keeping the automated beta release. The stable release is a manual script executed by maintainers.

# Backstage Architecture Decision Records

## Overview

The substantial architecture decisions made in the Backstage project live here. For more information about ADRs, when to write them, and why, please see [this blog post](https://engineering.atspotify.com/2020/04/when-should-i-write-an-architecture-decision-record/).

Records are never deleted but can be marked as superseded by new decisions or deprecated.

Records should be stored under the `architecture-decisions` directory.

### Contributing

#### Creating an ADR

- Copy `docs/architecture-decisions/adr000-template.md` to `docs/architecture-decisions/adr000-my-decision.md` (my-decision should be descriptive. Do not assign an ADR number.)
- Fill in the ADR following the guidelines in the template
- Submit a pull request
- Address and integrate feedback from the community
- Eventually, assign a number
- Add the path of the ADR to the microsite sidebar in [`sidebars.ts`](https://github.com/backstage/backstage/blob/master/microsite/sidebars.ts)
- Add the path of the ADR to the [`mkdocs.yml`](https://github.com/backstage/backstage/blob/master/mkdocs.yml)
- Merge the pull request

### Superseding an ADR

If an ADR supersedes an older ADR then the status of the older ADR is changed to "superseded by ADR-XXXX", and links to the new ADR.

## ADR001: Architecture Decision Record (ADR) log

### Decision

A decision was made to store ADRs in a log in the project repository.

### Discussion

There is a need to store big decisions made in a log as a reference point for the team, help with onboarding new members, and give context to others interested in the project.

### Risks

People stop adding ADRs to the log and context gets lost.

## ADR002: Default Software Catalog File Format

### Background

Backstage comes with software catalog functionality that you can use to track all your software components and more. It can be powered by data from various sources, and one of them that is included with the package is a custom database backed catalog. It has the ability to keep itself updated automatically based on the contents of little descriptor files in your version control system of choice. Developers create these files and maintain them side by side with their code, and the catalog system reacts accordingly.

This ADR describes the default format of these descriptor files.

#### Inspiration

Internally at Spotify, a homegrown software catalog system is used heavily and forms a core part of Backstage and other important pieces of the infrastructure. The user experience, learnings, and certain pieces of metadata from that catalog are being carried over to the open source effort.

The file format described herein also draws heavy inspiration from the [kubernetes object format](https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/).

#### Core Concepts

There are a number of descriptor files, all of whose locations (e.g., within a version control system) are registered with the software catalog. The method of registration is not covered in this document; it could happen either manually inside Backstage, or by push events from a CI/CD pipelines, or by webhook triggers from the version control system, etc.

Each file describes one or more entities in accordance with the [Backstage System Model](https://github.com/backstage/backstage/issues/390). All of these entities have a common structure and nomenclature, and they are stored in the software catalog from which they then can be queried.

Entities have distinct names, and they may reference each other by those names.

### Format

Descriptor files use the [YAML](https://yaml.org/spec/1.2/spec.html) format. They may be written by hand or created using automated tools. Each file may consist of several YAML documents (separated by `---`), where each document describes a single entity.

This is an example entity definition with some mocked data.

Code: --- ⏎ apiVersion: backstage.io/v1alpha1 ⏎ kind: Component ⏎ metadata: ⏎ name: frobs-awesome ⏎ description: | ⏎ Backend service that implements the Frobs API, as defined ⏎ in [the Frobs RFC](https://example.com/spec/frob.html). ⏎ labels: ⏎ system: frobs ⏎ lifecycle: production ⏎ example.com/service-discovery-name: frobsawesome ⏎ annotations: ⏎ circleci.com/project-slug: github/example-org/frobs-awesome ⏎ spec: ⏎ type: service

The root fields `apiVersion`, `kind`, `metadata`, and `spec` are part of the _envelope_, defining the overall structure of all kinds of entities. Likewise, the `name`, `namespace`, `labels`, and `annotations` metadata fields are of special significance and have reserved purposes and distinct shapes.

See below for details about these fields.

### Envelope

The root envelope object has the following structure.

#### `apiVersion` and `kind`

The `kind` is the high level entity type being described, typically from the [Backstage system model](https://github.com/backstage/backstage/issues/390). The first versions of the catalog will focus on the `Component` kind.

The `apiVersion` is the version of the specification format for that particular entity that this file is written against. The version is used for being able to evolve the format, and the tuple of `apiVersion` and `kind` should be enough for a parser to know how to interpret the contents of the rest of the document.

Backstage specific entities have an `apiVersion` that is prefixed with `backstage.io/`, to distinguish them from other types of objects that share the same type of structure. This may be relevant when co-hosting these specifications with, e.g., Kubernetes object manifests.

Early versions of the catalog will be using alpha/beta versions, e.g., `backstage.io/v1alpha1` to signal that the format may still change. After that, we will be using `backstage.io/v1` and up.

#### `metadata`

A structure that contains metadata about the entity, i.e., things that aren't directly part of the entity specification itself. See below for more details about this structure.

#### `spec`

The actual specification data that describes the entity.

The precise structure of the `spec` depends on the `apiVersion` and `kind` combination, and some kinds may not even have a `spec` at all. See further down in this document for the specification structure of specific kinds.

### Metadata

The `metadata` root field has the following nested structure.

#### `name`

The name of the entity. This name is both meant for human eyes to recognize the entity, and for machines and other components to reference the entity (e.g. in URLs or from other entity specification files).

Names must be unique per kind, within a given namespace (if specified), at any point in time. This uniqueness constraint is also case insensitive. Names may be reused at a later time, after an entity is deleted from the registry.

Names are required to follow a certain format. Entities that do not follow those rules will not be accepted for registration in the catalog. The ruleset is configurable to fit your organization's needs, but the default behavior is as follows.

- Strings of length at least 1, and at most 63
- Must consist of sequences of `[a-z0-9A-Z]` possibly separated by one of `[-_.]`

Example: `visits-tracking-service`, `CircleciBuildsDs_avro_gcs`

#### `namespace`

The `name` of a namespace that the entity belongs to. This field is optional and currently has no special semantics apart from bounding the name uniqueness constraint if specified. It is reserved for future use and may get broader semantic implication.

Namespaces may also be part of the catalog and are `v1` / `Namespace` entities, i.e., not Backstage specific but the same as in Kubernetes.

#### `description`

A human readable description of the entity to be shown in Backstage. Should be kept short and informative, suitable to give an overview of the entity's purpose at a glance. More detailed explanations and documentation should be placed elsewhere.

#### `labels`

Labels are optional key/value pairs that are attached to the entity, and their use is identical to [kubernetes object labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/).

Their main purpose is for references to other entities and for information that is in one way or another classifying for the current entity. They are often used as values in queries or filters.

Both the key and the value are strings, subject to the following restrictions.

Keys have an optional prefix followed by a slash, and then the name part, which is required. The prefix must be a valid lowercase domain name, at most 253 characters in total. The name part must be sequences of `[a-zA-Z0-9]` separated by any of `[-_.]`, at most 63 characters in total.

The `backstage.io/` prefix is reserved for use by Backstage core components. Some keys, such as `system` also have predefined semantics.

Values are strings that follow the same restrictions as `name` above.

#### `annotations`

An object with arbitrary non-identifying metadata attached to the entity, identical in use to [kubernetes object annotations](https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/).

Their purpose is mainly, but not limited, to reference into external systems. This could, for example, be a reference to the git ref the entity was ingested from, to monitoring and logging systems, to pagerduty schedules, etc.

Both the key and the value are strings, subject to the following restrictions.

Keys have an optional prefix followed by a slash, and then the name part, which is required. The prefix must be a valid lowercase domain name, at most 253 characters in total. The name part must be sequences of `[a-zA-Z0-9]` separated by any of `[-_.]`, at most 63 characters in total.

The `backstage.io/` prefix is reserved for use by Backstage core components.

Values can be of any length but are limited to being strings.

### Component

- Field | Value
- `apiVersion` | `backstage.io/v1alpha1`
- `kind` | `Component`

The `spec` object for this kind is as follows:

- Field | Type | Required | Description
- `type` | String | Yes | The type of component, e.g. `service`.

## ADR003: Avoid Default Exports and Prefer Named Exports

### Context

When CommonJS was the primary authoring format, the best practice was to export only one thing from a module using the `module.exports = ...` format. This aligned with the [UNIX philosophy](https://en.wikipedia.org/wiki/Unix_philosophy) of "Do one thing well". The module would be consumed (`const localName = require('the-module');`) without having to know the internal structure.

Now, `ESModules` are the primary authoring format. They have numerous benefits, such as compile-time verification of exports and standards-defined semantics. They have a similar mechanism known as "default exports", which allows for a consumer to `import localName from 'the-module';`. This is implicitly the same as `import { default as localName } from 'the-module';`.

However, there are numerous reasons to avoid default exports, as documented by others before:

- <https://humanwhocodes.com/blog/2019/01/stop-using-default-exports-javascript-module/>

A summary:

- They add indirection by encouraging a developer to create local names for modules, increasing cognitive load and slowing down code comprehension: `import TheListThing from 'not-a-list-thing';`.
- They thwart tools, such as IDEs, that can automatically rename and refactor code.
- They promote typos and mistakes, as the imported member is completely up to the consuming developer to define.
- They are ugly in CommonJS interop, as the default property must be manually specified by the consumer. This is often hidden by Babel's module interop.
- They break re-exports due to name conflicts, forcing the developer to manually name each.

Using named exports helps prevent needing to rename symbols, which has myriad benefits. A few are:

- IDE tools like "Find All References" and the "Go To Definition" function.
- Manual codebase searching ("grep", etc) is easier with a unique symbol.

### Decision

We will stop using default exports except when absolutely necessary (such as [`React.lazy`](https://18.react.dev/reference/react/lazy) modules). A workaround exists for those that would prefer to never use `default`:

Code: const Component = React.lazy(() => ⏎ import('../path/to/Component').then(m => ({ default: m.Component })), ⏎ );

### Consequences

We will actively work to remove them from our codebases, being as explicit as possible. Have a connected component? `export const ConnectedComponent = connect(Component)`.

We will add tools, such as lint rules, to help migrate away from default exports.

## ADR004: Module Export Structure

### Context

With a growing number of exports of packages like `@backstage/core-components`, it is becoming more and more difficult to answer questions such as

> Is the export in this module also exported by the package?

or

> What is exported from this directory?

We currently do not use any pattern for how to structure exports. There is a mix of package-level re-exports deep into the directory tree, shallow re-exports for each directory, exports using `*` and explicit lists of each symbol, etc. The mix and lack of predictability make it difficult to reason about the boundaries of a module, and for example knowing whether it is safe to export a symbol in a given file.

### Decision

We will make each exported symbol traceable through index files all the way down to the root of the package, `src/index.ts`. Each index file will only re-export from its own immediate directory children, and only index files will have re-exports. This gives a file tree similar to this:

Code: index.ts ⏎ components/index.ts ⏎ /ComponentX/index.ts ⏎ /ComponentX.tsx ⏎ /SubComponentY.tsx ⏎ lib/index.ts ⏎ /UtilityX/index.ts ⏎ /UtilityX.ts ⏎ /helper.ts

To check whether for example `SubComponentY` is exported from the package, it should be possible to traverse the index files towards the root, starting at the adjacent one. If there is any index file that doesn't export the previous one, the symbol is not publicly exported. For example, if `components/ComponentX/index.ts` exports `SubComponentY`, but `components/index.ts` does not re-export `./ComponentX`, one should be certain that `SubComponentY` is not exported outside the package. This rule would be broken if for example the root `index.ts` re-exports `./components/ComponentX`

In addition, index files that are re-exporting other index files should always use wildcard form, that is:

Code: // in components/index.ts ⏎ export * from './ComponentX';

Index files that are re-exporting symbols from non-index files should always enumerate all exports, that is:

Code: // in components/ComponentX/index.ts ⏎ export { ComponentX } from './ComponentX'; ⏎ export type { ComponentXProps } from './ComponentX';

Internal cross-directory imports are allowed from non-index modules to index modules, for example:

Code: // in components/ComponentX/ComponentX.tsx ⏎ import { UtilityX } from '../../lib/UtilityX';

Imports that bypass an index file are discouraged, but may sometimes be necessary, for example:

Code: // in components/ComponentX/ComponentX.tsx ⏎ import { helperFunc } from '../../lib/UtilityX/helper';

### Consequences

We will actively work to rework the export structure in our codebase, prioritizing the library packages such as `@backstage/core-components` and `@backstage/backend-common`.

If possible, we will add tools, such as lint rules, to help enforce the export structure.

## ADR005: Catalog Core Entities

### Context

We want to standardize on a few core entities that we are tracking in the Backstage catalog. This allows us to build specific plugins around them.

### Decision

Backstage should eventually support the following core entities:

- **Components** are individual pieces of software
- **APIs** are the boundaries between different components
- **Resources** are physical or virtual infrastructure needed to operate a component

![Catalog Core Entities](../assets/architecture-decisions/catalog-core-entities.png)

For now, we'll start by only implementing support for the Component entity in the Backstage catalog. This can later be extended to APIs, Resources and other potentially useful entities.

#### Component

A component is a piece of software, for example a mobile application feature, web site, backend service or data pipeline (list not exhaustive). A component can be tracked in source control, or use some existing open source or commercial software. It can implement APIs for other components to consume. In turn it might depend on APIs implemented by other components, or resources that are attached to it at runtime.

Component entities are typically defined in YAML descriptor files next to the code of the component, and could look like this (actual schema will evolve):

Code: apiVersion: backstage.io/v1alpha1 ⏎ kind: Component ⏎ metadata: ⏎ name: my-component-name ⏎ spec: ⏎ type: service

#### API

APIs form an abstraction that allows large software ecosystems to scale. Thus, APIs are a first class citizen in the Backstage model and the primary way to discover existing functionality in the ecosystem.

APIs are implemented by components and make their boundaries explicit. They might be defined using an RPC IDL (e.g. in Protobuf, GraphQL or similar), a data schema (e.g. in Avro, TFRecord or similar), or as code interfaces (e.g. framework APIs in Swift, Kotlin, Java, C++, TypeScript etc). In any case, APIs exposed by components need to be in a known machine-readable format so we can build further tooling and analysis on top.

APIs are typically indexed from existing definitions in source control and thus wouldn't need their own descriptor files, but would be stored in the catalog somewhat like this (actual schema will evolve):

Code: apiVersion: backstage.io/v1alpha1 ⏎ kind: API ⏎ metadata: ⏎ name: my-component-api ⏎ spec: ⏎ type: grpc ⏎ definition: > ⏎ service HelloService { ⏎ rpc SayHello (HelloRequest) returns (HelloResponse); ⏎ } ⏎ message HelloRequest { ⏎ string greeting = 1; ⏎ } ⏎ message HelloResponse { ⏎ string reply = 1; ⏎ }

#### Resource

Resources are the infrastructure your software needs to operate at runtime like Bigtable databases, Pub/Sub topics, S3 buckets or CDNs. Modelling them together with components and APIs will allow us to visualize and create tooling around them in Backstage.

Resources are typically indexed from declarative definitions (e.g. Terraform, GCP Config Connector, AWS Cloud Formation) and/or inventories from cloud providers (e.g. GCP Asset Inventory) and thus wouldn't need their own descriptor files, but would be stored in the catalog somewhat like this (actual schema will evolve):

Code: apiVersion: backstage.io/v1alpha1 ⏎ kind: Resource ⏎ metadata: ⏎ name: my-component-db ⏎ spec: ⏎ type: gcp-spanner ⏎ url: spanner.googleapis.com/projects/prj/instances/my-component-db/databases/my-db

### Consequences

We will continue fleshing out support for the Component entity in the Backstage catalog.

## ADR006: Avoid React.FC and React.SFC

### Context

Facebook has removed `React.FC` from their base template for a TypeScript project. The reason for this was that it was found to be an unnecessary feature with next to no benefits in combination with a few downsides.

The main reasons were:

- **children props** were implicitly added
- **Generic Type** was not supported on children

Read more about the removal in [this PR](https://github.com/facebook/create-react-app/pull/8177).

### Decision

To keep our codebase up to date, we have decided that `React.FC` and `React.SFC` should be avoided in our codebase when adding new code.

Here is an example:

Code: /* Avoid this: */ ⏎ type BadProps = { text: string }; ⏎ const BadComponent: FC<BadProps> = ({ text, children }) => ( ⏎ <div> ⏎ <div>{text}</div> ⏎ {children} ⏎ </div> ⏎ ); ⏎ /* Do this instead: */ ⏎ type GoodProps = { text: string; children?: React.ReactNode }; ⏎ const GoodComponent = ({ text, children }: GoodProps) => ( ⏎ <div> ⏎ <div>{text}</div> ⏎ {children} ⏎ </div> ⏎ ); ⏎ /* Or as a shorthand, if no specific child type is required */ ⏎ type GoodProps = PropsWithChildren<{ text: string }>; ⏎ const GoodComponent = ({ text, children }: GoodProps) => ( ⏎ <div> ⏎ <div>{text}</div> ⏎ {children} ⏎ </div> ⏎ );

### Consequences

We will gradually remove the current usage of `React.FC` and `React.SFC` from our codebase.

## ADR007: Use MSW to mock http requests

### Context

Network request mocking can be a total pain sometimes, in all different types of tests, unit tests to e2e tests always have their own implementation of mocking these requests. There's been traction in the outer community towards using this library to mock network requests by using an express style declaration for routes. react-testing-library suggests using this library instead of mocking fetch directly whether this be in a browser or in node.

<https://github.com/mswjs/msw>

### Decision

Moving forward, we have decided that any `fetch` or `XMLHTTPRequest` that happens, should be mocked by using `msw`.

Here is an example:

Code: import { http, HttpResponse } from 'msw'; ⏎ import { setupWorker } from 'msw/browser'; ⏎ const worker = setupWorker( ⏎ http.get('*/user/:userId', () => { ⏎ return HttpResponse.json({ ⏎ firstName: 'John', ⏎ lastName: 'Maverick', ⏎ }); ⏎ }), ⏎ ); ⏎ // Start the Mock Service Worker ⏎ worker.start();

and in a more real life scenario, taken from [CatalogClient.test.ts](https://github.com/backstage/backstage/blob/f3245c4f8f0b6b2625c4a6d5d50161b612fb4757/plugins/catalog/src/api/CatalogClient.test.ts)

Code: beforeEach(() => { ⏎ server.use( ⏎ http.get(`${mockApiOrigin}${mockBasePath}/entities`, () => { ⏎ return HttpResponse.json(defaultResponse); ⏎ }), ⏎ ); ⏎ }); ⏎ it('should entities from correct endpoint', async () => { ⏎ const entities = await client.getEntities(); ⏎ expect(entities).toEqual(defaultResponse); ⏎ });

### Consequences

- A little more code to write
- Gradually will replace the codebase with `msw`

## ADR008: Default Catalog File Name

### Background

While the spec for the catalog file format is well described in [ADR002](./adr002-default-catalog-file-format.md), guidance was not provided as to the name of the catalog file.

Following discussion in [Issue 1822](https://github.com/backstage/backstage/pull/1822#pullrequestreview-461253670), a decision was made.

### Name

The catalog file should be named

Code: catalog-info.yaml

This name is a default, **not a requirement**. The catalog file will work with Backstage regardless of its name.

## ADR009: Entity References

### Background

While the spec for the catalog file format is well described in [ADR002](./adr002-default-catalog-file-format.md), guidance was not provided as to how one is expected to express references to other entities in the catalog. There was also some confusion on how to reference entities in URLs in the Backstage frontend.

Following discussion in [Issue 1947](https://github.com/backstage/backstage/issues/1947), a decision was made.

### Entity References in YAML files

The textual format, as written by humans, to reference entities by name is on the following form, where square brackets denote optionality:

Code: [<kind>:][<namespace>/]<name>

That is, it is composed of between one and three parts in this specific order, without any additional encoding, with those exact separator characters. Optionality of `kind` and `namespace` are contextual, and they may or may not have default contextual fallback values.

When that format is insufficient or when machine made interchange formats wish to express such relations in a more expressive form, a nested structure on the following form can be used:

Code: kind: <kind> ⏎ namespace: <namespace> ⏎ name: <name>

Of these, only `name` is always required. Optionality of `kind` and `namespace` are contextual, and they may or may not have default contextual fallback values. All other possible key values in this structure are reserved for future use.

A system or user wanting to express a full entity name that is always valid shall supply the entire triplet, whether using the string form or the compound form.

A full description of the format can be found [in the documentation](https://backstage.io/docs/features/software-catalog/references).

### Entity References in URLs

Where entities are referenced by name in the Backstage frontend, the URL containing the reference shall take the following form:

Code: :namespace/:kind/:name

All three parts are required under all circumstances. The default value for the `namespace` in the catalog is the string `"default"` if the entity does not specify one explicitly in `metadata.namespace`.

This means that we do not encourage the string form of entity references to be used as a single URL segment, due to the use of URL-unsafe characters leading to possible risk, confusion, and uglier URLs.

## ADR010: Use the Luxon Date Library

### Context

Date formatting (e.g. `a day ago`) and calculations are common within Backstage. Some of these useful features are not supported by the standard JavaScript `Date` object. The popular [Moment.js](https://momentjs.com/) library has been commonly used to fill this gap but is affected by large bundle sizes and mutable state issues. On top of this, `momentjs` is [being sunset](https://momentjs.com/docs/#/-project-status/) and the project recommends using one of the more modern alternative libraries.

See [[RFC] Standardized Date & Time Library](https://github.com/backstage/backstage/issues/3401).

### Decision

We will use [Luxon](https://moment.github.io/luxon/index.html) as the standard date library within Backstage.

`Luxon` provides a similar feature set and API to `Moment.js`, but improves on its design through immutability and the usage of modern JavaScript APIs (e.g. `Intl`). This results in smaller bundle sizes while providing a full feature set and avoids the need for using additional libraries for common date & time tasks.

### Consequences

- All core packages and plugins within Backstage should use `Luxon` for any date manipulation or formatting that cannot be easily accomplished with the native JavaScript `Date` object.
- Using a single date library avoids having to learn multiple library APIs
- Having a single date library will reduce bundle sizes

## ADR011: Plugin Package Structure

### Context

A core feature of Backstage is the extensibility via plugins. Even most of the core features are implemented as plugins. A plugin consists of one or multiple packages in the `plugins/` directory. Up till now, we have a simple conventions for naming plugin packages: Plugins are named `x`, with the option of having a related backend plugin called `x-backend` (where `x` is the plugin name, like `catalog` or `techdocs`). There is a need for sharing code between the frontend and backend of a plugin, between backend plugins, or components and hooks between different frontend plugins ([some examples](https://github.com/backstage/backstage/issues/3655#issuecomment-758166746)). This results in emerging plugin packages with shared code, like `packages/catalog-client` or `packages/techdocs-common`.

> There is a common phrase in software development: > [Naming things is hard](https://martinfowler.com/bliki/TwoHardThings.html)

To keep the contributed plugins consistent, this Architecture Decision Record provides rules for naming plugin packages.

### Decision

We will place all plugin related code in the `plugins/` directory. The `packages/` directory is reserved for core package of Backstage.

We follow this structure for plugin packages (where `x` is the plugin name, for example `catalog` or `techdocs`):

- `x`: Contains the main frontend code of the plugin.
- `x-module-<name>`: Contains optional modules related to the frontend plugin package.
- `x-backend`: Contains the main backend code of the plugin.
- `x-backend-module-<name>`: Contains optional modules related to the backend plugin package.
- `x-react`: Contains shared widgets, hooks and similar that both the plugin itself (`x`) and third-party frontend plugins can depend on.
- `x-node`: Contains utilities for backends that both the plugin backend itself (`x-backend`) and third-party backend plugins can depend on.
- `x-common`: An isomorphic package with platform agnostic models, clients, and utilities that all packages above or any third-party plugin package can depend on.

We prefix the package names with `@backstage/plugin-`.

This structure is based on a [suggestion in issue #3655](https://github.com/backstage/backstage/issues/3655#issuecomment-758166746).

### Consequences

We will actively migrate existing packages that are part of a plugin to the `plugins/` folder. This affects packages like:

- `packages/techdocs-common` which should be moved to `plugins/techdocs-node` and named `@backstage/plugin-techdocs-node`.
- `packages/catalog-client` which will be part of a future `plugins/catalog-common` and named `@backstage/plugin-catalog-common`.
- While the new location of `packages/catalog-model` should be `plugins/catalog-common` we might want to do an exception here, as it's a very central package.

We will actively migrate optional features of backend plugins into separate `x-backend-module-<name>` packages, for example the more specialized processors in the catalog backend.

The limited set of rules might not be sufficient in the future. If additional packages are required, we will revisit this decision and extend the pattern.

If possible, we will add tools, such as lint rules, to help enforce the package names and dependencies between them or CLI commands to generate these packages.

The distinction between core packages and plugins helps us to setup [CODEOWNERS](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/about-code-owners) in the repository. We can set the code owners for the `packages/` folder to the core team and create additional rules (like `plugins/x*`) for plugin maintainers.

## ADR012: Use Luxon.toLocaleString and date/time presets

### Context

User's locales will have their own style of reading dates. It's counter intuitive to not have dates formatted in their familiar formats, it can cause users to have to think harder about what the date is and could even lead to interpreting dates incorrectly (e.g. 05/03/2021, this could be March 5th or May 3rd, depending on where the user is). At the moment, plugins are defining dates and times using custom formats and the `toFormat` method, which leads to inconsistent and unfamiliar formats.

### Decision

To keep the UI consistent and familiar to users, irrespective of their location, we have decided that we use `toLocaleString` and Luxon's [extensive list](https://github.com/moment/luxon/blob/master/docs/formatting.md#presets) of Date and Time presets.

Here is an example:

Code: const date = new luxon.DateTime(); ⏎ /* Avoid this: */ ⏎ date.toFormat('yyyy LLL dd'); // 2014 Aug 06 ⏎ date.toFormat('yyyy LLL dd hh:mm'); // 2014 Aug 06 12:01 ⏎ /* Do this instead: */ ⏎ date.toLocaleString(luxon.DateTime.DATE_MED); // US: Oct 14, 1983 | FR: 14 oct. 1983 ⏎ date.toLocaleString(luxon.DateTime.DATETIME_MED); // US: Oct 14, 1983, 9:30 | FR: 14 oct. 1983 9:30

### Consequences

- We will need to audit the current places Date/Times are being displayed in the UI and update them to follow this ADR.
- We will need to keep in mind for reviewing PRs going forward to follow this ADR, or find/create a linting rule to automate this in the review process.

## ADR013: [superseded] Proper use of HTTP fetching libraries

Note (Superseded):

This ADR has been superseded by [ADR014](./adr014-use-fetch.md) and no longer applies.

Note (:::):

### Context

Using multiple HTTP packages for data fetching increases the complexity and the support burden of keeping said package up to date.

### Decision

Backend (node) packages should use the `node-fetch` package for HTTP data fetching. Example:

Code: import fetch from 'node-fetch'; ⏎ import { ResponseError } from '@backstage/errors'; ⏎ const response = await fetch('https://example.com/api/v1/users.json'); ⏎ if (!response.ok) { ⏎ throw await ResponseError.fromResponse(response); ⏎ } ⏎ const users = await response.json();

Frontend plugins and packages should prefer to use the [`fetchApiRef`](https://backstage.io/api/stable/variables/_backstage_core-plugin-api.index.fetchApiRef.html). It uses `cross-fetch` internally. Example:

Code: import { useApi } from '@backstage/core-plugin-api'; ⏎ // Inside some functional React component... ⏎ const { fetch } = useApi(fetchApiRef); ⏎ const response = await fetch('https://example.com/api/v1/users.json'); ⏎ if (!response.ok) { ⏎ throw await ResponseError.fromResponse(response); ⏎ } ⏎ const users = await response.json();

Isomorphic packages should have a dependency on the `cross-fetch` package for mocking and type definitions. Preferably, classes and functions in isomorphic packages should accept an argument of type `typeof fetch` to let callers supply their preferred implementation of `fetch`. This lets them adorn the calls with auth or other information, and track metrics etc, in a cross-platform way. Example:

Code: import crossFetch from 'cross-fetch'; ⏎ export class MyClient { ⏎ private readonly fetch: typeof crossFetch; ⏎ constructor(options: { fetch?: typeof crossFetch }) { ⏎ this.fetch = options.fetch || crossFetch; ⏎ } ⏎ async users() { ⏎ return await this.fetch('https://example.com/api/v1/users.json'); ⏎ } ⏎ }

### Consequences

We will gradually transition away from third party packages such as `axios`, `got` and others. Once we have transitioned to `node-fetch` we will add lint rules to enforce this decision.

## ADR014: Proper use of HTTP fetching libraries

### Context

Until now we have been recommending the use of `node-fetch` in Node.js contexts through [ADR013](./adr013-use-node-fetch.md). Since then, Backstage has had its minimum requirements upgraded to Node.js 20 or newer. The Node.js platform has established a stable, reliable `undici` based native `fetch` in these versions. Additionally, there are [some issues](https://github.com/backstage/backstage/issues/24590) with using third party libraries that only appeared in newer versions of Node.js.

### Decision

All code that is executed in Node.js (including backend and CLIs) should use the native `fetch` for HTTP data fetching, and `typeof fetch` as the TypeScript type in code where a `fetch` implementation can be injected or is referred to. Example:

Code: import { ResponseError } from '@backstage/errors'; ⏎ // this is implicitly global.fetch ⏎ const response = await fetch('https://example.com/api/v1/users.json'); ⏎ if (!response.ok) { ⏎ throw await ResponseError.fromResponse(response); ⏎ } ⏎ const users = await response.json();

Frontend plugins and packages should prefer to use the [`fetchApiRef`](https://backstage.io/api/stable/variables/_backstage_core-plugin-api.index.fetchApiRef.html).

Code: import { useApi } from '@backstage/core-plugin-api'; ⏎ // Inside some React component... ⏎ const { fetch } = useApi(fetchApiRef); ⏎ const response = await fetch('https://example.com/api/v1/users.json'); ⏎ if (!response.ok) { ⏎ throw await ResponseError.fromResponse(response); ⏎ } ⏎ const users = await response.json();

Isomorphic packages should have a dependency on the `cross-fetch` package for mocking and type definitions. Preferably, classes and functions in isomorphic packages should accept an argument of type `typeof fetch` to let callers supply their preferred implementation of `fetch`. This lets them adorn the calls with auth or other information, and track metrics etc, in a cross-platform way. Example:

Code: import crossFetch from 'cross-fetch'; ⏎ export class MyClient { ⏎ private readonly fetch: typeof crossFetch; ⏎ constructor(options: { fetch?: typeof crossFetch }) { ⏎ this.fetch = options.fetch || crossFetch; ⏎ } ⏎ async users() { ⏎ return await this.fetch('https://example.com/api/v1/users.json'); ⏎ } ⏎ }

### Consequences

We will gradually transition away from third party `fetch` replacement packages such as `node-fetch` and others on the Node.js platform.

The `@mswjs/interceptors` library as used by `msw` version 1.x [does not support native fetch properly](https://github.com/mswjs/msw/issues/1563#issuecomment-1694249010) and likely never will. When you switch to using native fetch, you may see `msw` based tests start to fail to both capture and block traffic. Certain tests may need to be rewritten to use `msw` 2.x or newer instead, which uses a newer version of the interceptors.

## ADR015: Types and naming for element and component options

### Context

Until now there hasn't been a clear standard for how to define options that are intended to provide JSX elements or components. This led to a mix of different patterns in public APIs, which this ADR aims to standardize.

### Decision

We will use one of the following option property names and types when defining options that are intended to provide JSX elements or components:

#### Simple element

This option is used when a simple synchronous JSX element is provided. It must only be used in areas where lazy-loading is not needed.

Code: { ⏎ element: JSX.Element; ⏎ }

#### Simple component

This option is used when a simple synchronous component is provided. It must only be used in areas where lazy-loading is not needed.

Code: { ⏎ component: (props: { ... }) => JSX.Element | null ⏎ }

#### Async element loader

This option is used when a simple asynchronous JSX element is provided. It is the preferred option when only producing a single instance and there is no need to pass properties to the component. This format simplifies the creation of closures for passing additional properties in the loader implementation.

Code: { ⏎ loader: () => Promise<JSX.Element>; ⏎ }

#### Async component loader

This option is used when a simple asynchronous component is provided. It is the preferred option when properties need to be passed to the component or multiple instance are needed, and lazy-loading is required.

Code: { ⏎ loader: () => Promise<(props: { ... }) => JSX.Element | null> ⏎ }

#### Any component loader

This option is used in the same cases as the async component loader, but when the option of synchronous loading is also needed. The structure of always having the outer loader function, even in the synchronous case, makes it possible to determine the type of the loader at runtime.

Code: { ⏎ loader: (() => props => JSX.Element | null) | (() => Promise<props => JSX.Element | null>) ⏎ }

Note that when consuming this loader we'll need to unconditionally wrap it with `React.lazy`. This is because you can't delay the call to `React.lazy` until rendering, because you're not allowed to call it within a render function. This means that we can't first call the loader to check whether the returned value is a promise or not, and we must instead unconditionally wrap it with `React.lazy`. Therefore the implementation of accepting one of these loaders as an option needs to look something like this:

Code: const LazyComponent = React.lazy(() => ⏎ Promise.resolve(options.loader()).then(loaded => ({ default: loaded })), ⏎ );

### Consequences

We will update all APIs for the new frontend system in the `@backstage/frontend-*` packages.

We will not update any of the existing APIs for the old frontend system in the `@backstage/core-*` packages.

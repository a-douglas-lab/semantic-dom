# GOV.UK AWS Architecture Decision Records

## 1. Record architecture decisions

Date: 2017-06-30

### Status

Accepted

### Context

We need to record the architectural decisions made on this project.

### Decision

We will use Architecture Decision Records, as described by Michael Nygard in [documenting architecture decisions](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)

### Consequences

See Michael Nygard's article, linked above. For a lightweight ADR toolset, see [Nat Pryce's adr-tools](https://github.com/npryce/adr-tools)

## 2. Hosting Platforms

Date: 2017-06-30

### Status

Accepted

### Context

We need to decide upon a platform to host the future GOV.UK infrastructure. Long term, this will be primarily the GOV.UK PaaS but in the interim, we need to converge with that plan and also upgrade and modernise the current infrastructure.

GDS policy for hosting of GDS internal services is PaaS first and AWS for anything that can not be run on the PaaS.

### Decision

We are using Amazon Web Services as our hosting provider of choice. This conforms to the [GDS Tech Forum Hosting Guide](https://github.com/alphagov/gds-tech/pull/7).

We will initially be using the `eu-west-1` region, Ireland. This region has 3 availability zones and also contains the GDS PaaS which will allow easier sharing and peering.

### Consequences

We will have to migrate our infrastructure from our current hosting provider to Amazon in the near-term "as-is" and then iterate on that infrastructure in the medium term to deliver improvements to the platform. This will also make a subsequent migration of applications to the PaaS more straightforward.

## 3. Networking Outline

Date: 2017-06-30

### Status

Partly superseded

### Context

As part of the migration to AWS we need to define our IP addressing strategy and assign ranges to different environments. We will attempt to keep the new IP layout as close as possible to the current one in order to ease migration. This is not completely possible due to Amazon AZs necessarily being on different subnets within the same VPC range.

This record does not currently cover the disaster recovery environments and treats CI as an embedded part of integration.

### Decision

- 1 VPC per environment (currently integration, staging and production)
- 3 public subnets, spread across availability zones
- 3 private subnets, spread across availability zones

**These IP ranges have been superseded by [ADR #0033](0033-ip-ranges.md).**

The VPCs will be assigned the following IP ranges:

- Environment | IP Range
- Integration | 10.1.0.0/16
- Staging | 10.2.0.0/16
- Production | 10.3.0.0/16
- Test | 10.200.0.0/16

Each AZ shall be a `/24` within the above ranges.

eg. Integration - AZ1: 10.1.1.0/24, AZ2: 10.1.2.0/24, AZ3: 10.1.3.0/24

We will be deliberately flattening the current VDC separation and placing all the hosts in a private subnet per availability zone and using security groups to maintain our current network isolation.

### Consequences

Disaster recovery environments will be addressed in a future ADR.

The extraction and isolation of the CI environments will be addressed in a future ADR once they have been confirmed to work in the current way - as part of integration.

## 4. DNS definitions for hosts and services

Date: 2017-07-14

### Status

Superseded by [DNS Infrastructure](0015-dns-infrastructure.md)

### Context

For our current monitoring to work we need Icinga to be able to communicate with hosts and services.

### Decision

Each stack will have an internal, private, zone for internal services such as the puppetmaster. These will be in the following format:

$servicename.$stackname.internal

puppet.perftesting.internal monitoring.mystack.internal

### Consequences

TBC

## 5. Terraform Module Location

Date: 2017-07-04

### Status

Accepted

### Context

Document structure and deployment of Terraform [modules](https://www.terraform.io/docs/modules/index.html).

Terraform can fetch modules from multiple [sources](https://www.terraform.io/docs/modules/sources.html) (e.g. Github, local files, S3).

### Decision

Whilst developing a module we will source it locally (within this repository).

Once we feel our modules "ready" we will consider moving them to separate repositories.

### Consequences

Keeping modules locally will make them harder for others to use but make rapid iteration easier.

Once modules are separated we will need processes to propagate changes in dependent modules to our main Terraform projects.

## 6. Puppet architecture

Date: 2017-07-04

### Status

Pending

### Context

For our initial iteration we should discuss whether we use a Puppetmaster architecture, or use a masterless Puppet approach.

Using the former approach, we would have to take the following into account:

- We would set up a Puppetmaster for the rest of the provisioned instances to connect to
- We would deploy new Puppet code to this machine only
- It matches our current architecture and approach
- We would need to take into account certificate management
- Each machine would "check in" to the Puppetmaster every 30 minutes, ensuring a consistent state

If we used a masterless approach:

- We would need to deploy Puppet code and secrets to each instance that we provision
- We would run Puppet only when we deploy new code
- It differs from our current approach
- We would not have to manage a Puppetmaster which means no single point of failure

### Decision

Use a Puppetmaster to not diverge from current architecture in the initial iteration.

### Consequences

We may suffer from having to manage two Puppetmasters while we run in two environments.

There is additional work around the management of a Puppetmaster.

However, this matches our current working architecture so it means that we're more in line of doing a straight "lift and shift". In theory deployments would be more straight forward to manage as we would not have to create a new deployment process, instead we could amend the current deployment process.

## 7. Puppet certificate management

Date: 2017-07-04

### Status

Accepted

### Context

When machines connect to a Puppetmaster, they require a signed certificate to be present to allow interaction.

If we lose a Puppetmaster (or it is recreated by an Auto Scaling Group) then we would have to re-sign all the certificates to allow all machines in the environment to run Puppet again (ref: https://docs.puppet.com/puppet/3.8/ssl_regenerate_certificates.html).

This would involve manual intervention to allow machines to connect again and we would be unable to deploy new Puppet code during this period.

Ideally we should back up our signed certificates, and a new machine would be able to restore them when it is recreated.

### Decision

We will defer this until a later date while we're testing this with Integration to concentrate on getting the stack up and running and accept the loss of certicates.

At a later date we will re-visit this approach and implement a suitable solution.

### Consequences

If we lose our Puppetmaster while we are not backing up our certificates it may delay us while we have to regenerate certificates.

We will be able to focus on bringing up the environment rather than working on a solution that is not currently present in our Puppet code.

## 8. Postgres on Puppetmaster

Date: 2017-07-04

### Status

Accepted

### Context

We need to decide whether to run PostgreSQL on the Puppetmaster itself or use RDS from the off.

Currently our Puppetmaster uses a local PostgreSQL instance as its database. In moving to AWS we have the opportunity to replace this with an RDS instance.

This may remove a reasonable amount of puppet code used to configure the database and associated tasks (e.g. backups). It would also require an amount of Terraform work to provision the RDS instance and some updates to the Puppetmaster code to use that instance.

### Decision

The Puppetmaster will continue to use a local instance of PostgreSQL.

### Consequences

This should decrease the number of changes made to existing code.

This should reduce the amount of new work being done in Terraform.

We will not be able to use the Puppetmaster as a test-bed for RDS work.

We will maintain the existing puppet code.

We can continue to use existing backup & restore strategies.

## 9. Environment bootstrapping process

Date: 2017-07-04

### Status

Pending

### Context

We need a process to bootstrap a new Amazon environment. This should be both heavily automated and include set places where the operator can evaluate the status of the provisioning.

This bootstrapping process assumes the following:

- The required repositories are available
- An Amazon Web Services admin account is available
- Backups of our data can be retrieved (for the restore process)

### Decision

The chosen process has a few, early bootstrap steps, that differ from normal operations. These aim to quickly provide the usual level of self-service to allow teams to independently restore services without a dependency on a central operations team. An early draft of this process, which will be updated as changes are required, will be:

- 1. Clone all the relevant repositories
- 1. Build the S3 bucket for Terraform state
- 1. Provision the new DNS zones for this environment
- 1. Build the Puppet master
- 1. Deploy the puppet code and secrets
- 1. Build the deploy Jenkins
- Rebuild everything else in the usual deployment ways

This document will be written so that one of the non-infrastructure members of the team will be able to provision a complete environment within our allowed recovery time.

### Consequences

Having a well defined, documented, bootstrap process will allow us to test our business continuity plans, build special environments for things like performance testing and prevent drift between our version controlled and deployed infrastructure.

Providing the ability for non-technical specialists to build an environment will help to reassure our management team and auditors that our BCP/DR plans are both actionable and current.

## 10. Terraform directory structure

Date: 2017-07-04

### Status

Accepted

Amended by [17. Terraform Data Structure](0017-terraform-data-structure.md)

### Context

We should have a consistent directory structure for Terraform from the beginning.

Some initial requirements:

- We want to separate code from data, so in the future we can open source the code without disclosing our implementation details,

maybe keeping the data in a private Github repository

- We want to be able to encrypt sensitive data in the repository: we want to support sensitive data encryption as part of the same

process, without having to manage secrets in a different repository, with different scripts, etc.

- We want to create Terraform modules to reuse code
- We want to separate Terraform code into different projects, each one managing an infrastructure tier or application stack. This

is especially important to separate resources between GOV.UK applications.

### Decision

The initial solution presents three directories: data, modules and projects:

- The data directory contains a subdirectory per Terraform project, to store variable values that can be customised per environment.
- The data directory also contains \_secrets files with sensitive data encrypted with 'sops'
- The modules directory contains a subdirectory per Terraform provider
- The projects directory contains the Terraform stacks/tiers
- Projects will be named such that:
- Those to deploy common infrastructure will have a `govuk` prefix (e.g. networking, DNS zones)
- Those to deploy applications (or groups of applications) will have an `app` prefix (e.g. frontend, puppetmaster).

Code: ├── data ⏎ │   ├── base ⏎ │   │   ├── common.tfvars ⏎ │   │   └── integration.tfvars ⏎ │   └── my-application ⏎ │       ├── common.tfvars ⏎ │       ├── integration.tfvars ⏎ │       └── integration_secrets.json ⏎ ├── modules ⏎ │   └── aws ⏎ │       ├── route53_zone ⏎ │       │   └──  ... ⏎ │       ├── mysql_database_instance ⏎ │       │   ├── ... ⏎ │       └── network ⏎ │           └── ... ⏎ └── projects ⏎ ├── base ⏎ │   ├── integration.backend ⏎ │   ├── main.tf ⏎ │   └── variables.tf ⏎ └── my-application ⏎ ├── integration.backend ⏎ ├── main.tf ⏎ └── variables.tf

### Consequences

If we manage secrets as explained before, we are going to have to decrypt the secrets files at run time and make sure we clean up unencrypted files after running the Terraform commands.

This set up requires relative paths to import modules in the Terraform stacks that depend on the directory from where we are initialising the project. So once we feel comfortable with our modules, we'll need to consider to put them on Github repositories so we can source them from the Terraform stacks via URL.

## 11. Migration Strategy

Date: 2017-07-04

### Status

Accepted

### Context

Two strategies were considered for the "lift and shift" aspect of this work. This is to clarify what those two options were and what was considered in the process of making the decision.

- 1) Migrate an environment to AWS step-by-step in groups of applications at a time - eg. frontends, then backends or even finer groupings, and building the infrastructure as we go.
- 2) Provision and configure the entire environment, deploy all applications, restore all databases and other data and then switchover to using the new environment in one go - a small maintenance window is necessary to sync data and switch DNS.

### Decision

The second option - all in one go - was decided because:

a) The change is atomic. Either the environment is live in AWS or it's live in the current environment. This is much easier to manage than having elements of the environment in two places and having two sets of monitoring, Puppet masters, metrics etc.

b) Related to a) - unless there is a very strict migration plan with dates and deadlines, we risk running on two platforms with all the extra work that creates for a long period of time if we don't migrate atomically.

c) Higher flexibility to test tearing down and bringing up stacks in their entirety without affecting a live service. That is, no test stack will require any infrastructure from the existing hosting platform to support it.

d) This method much more accurately mirrors a DR situation and so this migration to AWS also doubles as DR preparation and rehearsal as complete environments are built, tested, removed and built again continuously over the course of the task.

### Consequences

- Less planning is required as we can entirely concentrate on getting the core applications running on Integration without risk of anything affecting a live service
- There will need to be a maintenance window for the actual switchover and out-of-hours work to action this.
- During the testing phase, there will be an increase in costs as the full stack is maintained on the current platform as well as a full stack in AWS.

## 12. Security Groups in Terraform

Date: 2017-07-05

### Status

Accepted

### Context

There are two methods of defining security groups for AWS in Terraform and they are distinguished by how you add rules: in-line and separate. Using in-line rules keeps the definition close to the resource but when ever a rule is changed Terraform will re-generate the entire resource. Using separate rules Terraform will only make the single rule change but there is greater boilerplate and separation between the group resource and the rule resource.

### Decision

Security groups will be defined separate to their rules.

Additionally each security group will be defined, in its entirety, in a single file.

### Consequences

Terraform should only create the specific rules that have changed when run.

There will be a larger 'distance' between the definition of a group and its rules.

Separate files may be harder to follow if there is heavy cross-referencing of security groups.

There may be a performance impact to Terraform depending on how it treats forward references.

## 13. Userdata provisioning snippets

Date: 2017-07-14

### Status

Pending

### Context

Our provisioning process with Terraform uses a user_data script to customise the installation during the instance initialisation. Parts of this customisation will be common to most projects, for instance, install the puppet client, apply package updates, add external disks, etc.

At the moment, the node_group module takes a parameter for a default user_data script, and optionally accepts another parameter for an additional script that is appended to the default one. We've been adding common customisation to the default user_data script in the node_group module, and adding similar code in additional user_data scripts within the project modules.

This is a problem because the default user_data script in the node_group module is becoming very specific for GOV.UK use, and we are repeating a lot of code in the additional user_data scripts.

### Decision

Add a userdata-snippets directory to the root Terraform directory with parts of scripts that can be concatenated to create the additional user_data script for each project. We can use a variable that accepts a list of parts that need to be concatenated so the final script can be customised for each project.

All the user_data snippets live in this directory so we can easily locate and maintain provisioning scripts.

The default user_data script in the node_group module should be very generic, probably just a header for the type of script we are appending afterwards.

### Consequences

We are adding a little bit of logic to the project code to evaluate the variable with the list of snippets and concatenate the parts into the additional_user_data parameter passed to the node_group module.

The snippet scripts need to use a numeric prefix to make sure parts are concatenated in the right order.

## 14. Launch Config change propagation process

Date: 2017-07-14

### Status

Accepted

### Context

An Auto-scaling Group's (ASG) instances are all created using a Launch Configuration (LC). The LC manages the image used to build instances as well as any user-data, security groups or tags.

When the LC of an ASG is changed those changes are only propagated to new instances. New instances are only created if the ASG scales-out or if an existing instance goes away (e.g. is terminated or fails).

Historically many of our instances are long lived (e.g. production puppetmaster, at time of writing, has an uptime of 79 days). This means that changes to the LC may take a long time to propagate fully. In the case of important changes to the LC (e.g. new security groups or tags that add Puppet facts) this is undesirable.

There are several possible ways to force propagation of LC changes within the existing Terraform code were considered ([issue](https://github.com/hashicorp/terraform/issues/1552)):

- Manual termination of instances
- Embedding CloudFormation in Terraform to more tightly manage instance life-cycle ([e.g. see this comment](https://github.com/hashicorp/terraform/issues/1552#issuecomment-191847434))
- Creating a new ASG for every LC ([e.g. see this post](https://groups.google.com/forum/#!msg/terraform-tool/7Gdhv1OAc80/iNQ93riiLwAJ))

### Decision

In order to propagate LC changes we will manually terminate effected instances.

### Consequences

- Dev time that involves changing the LC may slow slightly or require further automation to enable rapid work on instances
- Our Terraform will remain simple
- ASGs will persist between LCs
- LC deploys will need to manage instance life-cycles

## 15. DNS infrastructure

Date: 2018-03-06

### Status

Accepted

### Context

- All our instances will need to be able to resolve internal infrastructure services, such

us Puppet, Graphite or Logstash

- Some services and application endpoints will need to be exposed to the Internet and

be resolved by public DNS. For instance alerts.integration, deploy.integration, www-origin, etc

- We want to be able to create new pieces of infrastructure alongside the current piece of infrastructure

with the ability to test direct access to each piece using DNS endpoints

- We want to control which stack is running the active version of a piece of infrastructure, and control

how applications connect using DNS

- We want to ensure the site and all links works correctly when users browse using the

publishing (publishing.service.gov.uk) domain.

### Decision

![DNS](./0015-govuk-aws-dns.jpg?raw=true "DNS Infrastructure")

##### Stack domains

Each stack has an internal and external DNS domain. All Terraform projects in that stack add records to Route53 zones to expose the service internally and/or externally.

For instance, a 'green' stack has its own `green.<internalrootdomain>` and `green.<externalrootdomain>` domain. Puppet and Icinga services in this stack will add `puppet.green.<internalrootdomain>` and `alerts.green.<externalrootdomain>` to Route53.

This is for an infrastructure level view only. Applications will not work correctly across independent stacks, and will only correctly work using the Publishing domain.

#### Root domain service records

All services will need an entry with the root domain that points to a stack record. This entry can be updated to select the active version of each service.

For instance, machines are using the Puppet service `puppet.<internalrootdomain>` that is a CNAME of `puppet.green.<internalrootdomain>`. At some point, a new Puppet stack 'blue' is provisioned to test a new version, and when it has been tested we switch the CNAME to the new stack, so `puppet.<internalrootdomain>` resolves to `puppet.blue.<internalrootdomain>`.

##### External Route53 zones

There is a public (external) Route53 zone to manage the external root domain. Each stack has also its own external Route53 zone where we delegate the stack subdomain.

For instance, if we are setting up a new environment with a public root domain `test.govuk.digital`, and create a new stack 'green', we'll have a zone for `test.govuk.digital` and a zone for the stack subdomain `green.test.govuk.digital`, that stores the stack records.

##### Internal Route53 zones

For internal domains we cannot replicate the external configuration because it's not possible to do DNS delegation with internal zones in the same VPC when the domains overlap.

For instance, for the previous scenario we will have an internal zone for the root domain `test.govuk-internal.digital`, but we cannot create and delegate a subdomain for a zone `green.test.govuk-internal.digital` in the same VPC because it overlaps the root domain.

In this case, for internal domains we can only have a single zone, but we'll still keep the same domain schema and each stack will generate records appending the stack subdomain.

### Consequences

Initially we need to manage the entries in the root domains manually.

## 16. internal DNS zones

Date: 2017-07-19

### Status

Accepted

### Context

We have a number of internal services that need to have internal only service records. This allows clients to connect within their own environment or stack without needing a fully qualified domain name.

These records should not be visible outside the local environment or stack.

### Decision

We've bought a domain name that will not be connected to the rest of the public DNS system. This will be used by our internal services.

This domain will *not* have DNS records added to it.

### Consequences

We have a domain that we pay for and don't use.

If the registration ever expires, and we've incorrectly defined our search paths, someone could register it and influence our services. This risk is however present in all the domains we use.

This is also the approach taken by some of our sister teams.

## 17. Terraform Data Structure

Date: 2017-07-14

### Status

Accepted

Amends [10. Terraform directory structure](0010-terraform-directory-structure.md)

### Context

Our various Terraform projects share a significant amount of similar configuration (e.g. remote state buckets, stackname).

Under [ADR 10](0010-terraform-directory-structure.md) this is repeated for every project and every stack.

### Decision

The data portion of ADR 0010 will now be:

Code: ├── data ⏎ │   ├── common ⏎ │   │   └── <environment> ⏎ │   │       ├── common.tfvars ⏎ │   │       └── <stackname>.tfvars ⏎ │   ├── <project> ⏎ │   │   └── <environment> ⏎ │   │       ├── common.tfvars ⏎ │   │       ├── <stackname>.tfvars ⏎ │   │       └── <stackname>_secrets.json

Where:

- `<environment>` is the account being deployed to (e.g. 'integration', 'staging')
- `<stackname>` is the specific collection of projects (e.g. 'integration-green', 'foo-test')
- `<project>` is the project describing the resources to build (e.g. 'puppetmaster', 'frontend')

The tfvar files will be applied in this order:

- `common/<environment>/common.tfvars`
- `common/<environment>/<stackname>.tfvars`
- `<project>/<environment>/common.tfvars`
- `<project>/<environment>/<stackname>.tfvars`
- `<project>/<environment>/<stackname>_secrets.tfvars`

### Consequences

- Values only need to be defined in one place

## 18. Use RDS instead of provisioned EC2 databases

Date: 2017-08-01

### Status

Accepted

### Context

We use both MySQL and PostgreSQL in our stack for different applications. These have been traditionally provisioned as VM instances and managed with Puppet.

Puppet manages every aspect of these instances:

- Server configuration and tuning
- CRUD actions on databases
- Users and permissions
- Replication/clustering
- Backups

AWS offers the [Relational Database Service](https://aws.amazon.com/rds/) (RDS).

Using RDS would remove the following away from being managed by Puppet:

- Server configuration and tuning
- Replication/clustering
- Backups

Terraform code would be required to ensure the above is configured correctly.

### Decision

We are going to use RDS to remove a significant portion of our Puppet code that traditionally managed both PostgreSQL and MySQL.

To manage databases, users, data loading and long-term offsite backups, we will create a new type of node class named "db_admin". This will be able to connect and configure each RDS instance in a stack.

### Consequences

New code will need to be written to create the "db_admin" class, and some rewriting of our logic will be required in Puppet.

We will need to understand and create relevant monitoring for RDS instances.

We will eventually be able to remove the large amount of Puppet code related to the management and provisioning of both MySQL and PostgreSQL servers.

## 19. Centralise MySQL Databases

Date: 2017-08-02

### Status

Accepted

### Context

We currently have a number of MySQL primaries, secondaries and backup machines managed via Puppet agents that run on the database nodes themselves. While we are currently moving the data stores to the managed RDS service there are some supporting functions, such as adding databases and users, that still need to be conducted by a config management running host.

An additional piece of context is that once the 'lift and shift' is done we will convert the signon application and database to PostgreSQL.

This ADR is to document where they will run in the future.

### Decision

We discussed three options:

- 1. have one admin instance per MySQL database and keep the databases separate
- 2. manage the users and databases in terraform itself
- 3. centralise the MySQL databases and have one admin machine manage them all

The first option is the simplest, has the most moving parts and the highest expense while also providing the greatest level of isolation. Due to the low amount of traffic most of the MySQL databases receive we decided against this due to cost and the number of instances it would require.

Option 2 was discounted as we do not want to manage individual aspects of databases and their users using Terraform providers at this date as we have a large, existing, investment in using puppet for these tasks. We would also need a way to pass secrets back and forth between the two code bases; a complexity we'd like to defer.

The final option, and the one we've chosen for now, is to have a single instance with a dedicated "db admin" puppet role that will manage these tasks for all of our databases while also centralising the databases themselves in to a single RDS instance in order to simplify our connectivity code, connection strings and secret management. This is also a much cheaper approach.

### Consequences

At this time our traffic is low enough that we can group all the databases together with some sense of capacity safety. We do acknowledge however that a performance issue with one of the databases would impact all of the applications.

We're also placing all our database eggs in a single basket. If we lost the RDS cluster multiple applications would be impacted. This is considered an acceptable risk for our current experiments.

The changes to our puppet code will all be additions, which reduces the risk of impacting our currently managed systems.

## 20. Merge API PostgreSQL instance into main PostgreSQL instance

Date: 2017-08-07

### Status

Accepted

### Context

The only database that runs on API PostgreSQL instances is Stagecraft, which is for the Performance Platform.

This is able to run on the main PostgreSQL instance as we do not have the split of "vDCs" that we have in our current hosting provider.

Work is ongoing to migrate the Performance Platform away from our infrastructure and to The Government PaaS, so the long term plan is not have this database in our infrastructure at all.

### Decision

We should merge the API PostgreSQL instance into the main PostgreSQL instance.

### Consequences

The application configuration will need to be updated to connect to the correct database.

We are able to reduce the amount of database instances we maintain.

## 21. Use ACM for SSL purchases and terminate certificates on ELBs

Date: 2017-08-14

### Status

Accepted

### Context

Traditionally to manage our SSL certificates, we did the following:

- Purchased SSL certificates from a third party company, and did manual renewals
- Set up monitoring so we were aware when a certificate needed to be renewed
- Terminated SSL using nginx on the frontend_lb and backend_lb machines

We have looked into using Amazon Certificate Manager (ACM) to purchase and manage our SSL certificates, and using Elastic Load Balancers (ELBs) to terminate the SSL in front of the instances.

### Decision

We have decided to use ACM to manage our SSL certificates, and terminate SSL on the ELBs.

This gives us the following advantages:

- Automatic renewal and notifications related to the SSL certificates we purchase through ACM
- Multi-domain certificates; this helps us manage several stacks within an environment eg *.blue.integration.govuk.digital, *.green.integration.govuk.digital
- Terminate SSL on ELBs means the deployment is managed through Terraform
- We reference the certificate by an ARN ID, rather than having the SSL private key and certificate be present in encrypted hieradata

### Consequences

Technically this may be considered vendor lock-in, but the advantages significantly outweigh the cost.

We can only manually create certificates in ACM so are unable to automate this process, but we accept the time cost of doing this step.

## 22. Remove the Elasticsearch proxy

Date: 2017-08-16

### Status

Accepted

### Context

We currently have a local nginx based proxy for Elasticsearch connections on a number of our machines. The original reason for this was:

Code: Load balance connections to Elasticsearch by creating a loopback-only ⏎ vhost in Nginx which will forward to a set of Elasticsearch servers. ⏎ This is for the benefit of applications with client libraries that don't ⏎ support native cluster awareness or load balancing.

In the AWS environments these services are behind an ELB so this layer may no longer be required.

### Decision

We've tested the instances in AWS without the local proxies and we have not discovered any degradation of service when using the ELBs. In light of this we will remove the configuration and exclude this puppet code from running in AWS and accept the ELBs as its replacement.

### Consequences

There will be a slight difference, considered by the team to be an improvement, between the current environments and the new, AWS ones. This means we won't be testing the exact same thing but will simplify the networking and application data flow paths.

## 23. Use separate data repository

Date: 2017-08-18

### Status

Accepted

### Context

We have a large amount of data which is needed to run the Terraform projects.

Some of the data we need to use is sensitive (e.g. RDS passwords). It is considered best practice to keep sensitive information encrypted in private repositories. This means that access can be controlled and the that the data will remain secure, even if it is accidentally published.

### Decision

The `terraform/data` directory will be split out into its own repository that will be kept private and all sensitive data within it will be encrypted using [sops](https://github.com/mozilla/sops).

### Consequences

Sensitive data will not be publicly available. Should it leak it will still be cryptographically protected.

The terraform build tool will need to be extended to deal with an external data directory.

Building the terraform project will require access to both the terraform and the data repositories.

## 24. AMI Lookups

Date: 2017-08-29

### Status

Accepted

### Context

All of our launch configs require that an Amazon Machine Image (AMI) be specified. How the AMI ID is specified is the point of debate.

Currently we use the `aws_ami` data source to determine the newest AMI ID published by Ubuntu within a major version and use that in our launch configurations. This ensures we're always using newest version of Ubuntu when we spin up a new set of machines. On the downside, as this can change without our intervention, our terraform runs sometimes want to change more than we would expect:

Code: image_id: "ami-2944as50" => "ami-10c9asa9" (forces new resource)

In some cases _this is fine_ but due to the legacy nature of our deployments it causes issues with machines that need a number of manual deployment steps applied to them. Examples of these include the app servers and the puppet master.

The other alternative is to specify a specific image name. This has the benefit that we know exactly which version we deploy and it cannot change without our intervention.

### Decision

We override the `instance_ami_filter_name` parameter of the `node_group` module in all the projects. In the data directory, there is a common variable that sets the default value of the parameter for an environment. This can be customised per project in the project tfvars file.

### Consequences

Moving away from the dynamic AMI lookup means we might deploy auto scaling groups with an older version of the AMI that could have more security issues present. We'd work around this in the same way we do our other environments; by using the overnight security patching we deploy via puppet.

## 25. Use Elasticache for Redis

Date: 2017-09-04

### Status

Accepted

### Context

Traditionally we provisioned our own redis machines in a non-clustered state.

AWS provide Elasticache which has a Redis engine, and can be configured to be clustered.

We should consider provisioning Elasticache to replace our provisioned Redis instances.

### Decision

We are using Elasticache instead of provisioning our own Redis instances.

### Consequences

We have less Puppet code to manage. There is no risk of lock-in because the client side behaviour is not changed.

There are some [restricted commands](http://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide/ClientConfig.RestrictedCommands.html) in Elasticache which may impact our management of it.

## 26. Remove load balancer tier

Date: 2017-08-16

### Status

Accepted

### Context

We currently have a dedicated tier of load balancers for the backend, frontend and api VDCs. In the Amazon world these are less useful as we also have ELBs in place to handle the autoscaling of instances. We want to reduce the networking complexity and remove these machines.

### Decision

We will not change the current vcloud based platforms.

In the AWS environment we will remove the load balancer hosts / ELBs and instead add external ELBs to a number of other autoscaling groups (such as the frontend / backend hosts themselves) to make them directly available, but security group restricted.

We have also decided to split the domains we use to an internal and external one. That is discussed in ADR TODO: TBC.

### Consequences

3 classes of machines, and the instances running them, will be removed from our architecture in this environment. Some of the LBs processing, such as trace ids, will be pushed down the stack to the application servers themselves. We will have more ELBs running for a period of time.

All traffic will go to the external domain names at this phase of the move. The ADR TODO: TBC will explain the risks and remediations for this change.

## 27. Move PublicAPI away from frontend-lb

Date: 2017-09-04

### Status

Accepted

### Context

Traffic flows for frontend applications in the following way:

![Frontend traffic flow](./0027-move-publicapi-away-from-frontend-lb-img01.jpg?raw=true "Frontend traffic flow")

Most frontend applications can go straight from the cache instances to the application instances, bypassing frontend-lb. They do this by creating a DNS entry for each application service ELB, and setting the appropriate upstream DNS entry for the nginx configuration on the cache machines.

The exception to this rule is the "publicapi" application ([reference](https://github.com/alphagov/govuk-puppet/blob/34c587b76abee63d0c84b9f67212ac2f1c65ba2e/modules/govuk/manifests/apps/publicapi.pp)).

This is a set of nginx configuration that sits on frontend-lb, and forwards specific paths to applications upstream.

Router on the cache instances forwards all traffic bound for `/api` to frontend-lb, and then publicapi handles the forwarding from there.

The configuration for the paths is [relatively simple](https://github.com/alphagov/govuk-puppet/blob/34c587b76abee63d0c84b9f67212ac2f1c65ba2e/modules/govuk/templates/publicapi_nginx_extra_config.erb).

### Decision

Move publicapi application to either the cache instances themselves, or replace the configuration with an Application Load Balancer.

### Consequences

The frontend-lb will be able to be removed from the stack.

## 28. Combine api-mongo cluster into mongo cluster

Date: 2017-09-14

### Status

Accepted

### Context

Traditionally we had 4 mongo clusters:

- api-mongo
- mongo
- performance-mongo
- router-backend

Each cluster is a set of 3 instances, and the way we have built it in AWS is with one machine in one AZ, in an ASG with it's own ELB. This was due to the way that mongo relies on hostnames to create and join a cluster.

Performance Platform is officially out of scope as it is moving to the Government PaaS.

The only application that uses the api-mongo cluster is Content Store.

The router-backend cluster is used by Router. This should remain independent due to the critical nature of this application.

All other applications use the mongo cluster.

### Decision

We are going to remove the api-mongo cluster, and update Content Store so it reads from the application mongo cluster.

### Consequences

There is a chance that the main application mongo cluster becomes a point of failure across the entire stack when several applications depend on it. Content Store is critical for many frontend applications, and so there will be increased load on that cluster.

Removing the api-mongo cluster will simplify our architecture, and save money.

## 29. Combine api-redis into backend-redis

Date: 2017-09-14

### Status

Accepted

### Context

We currently have 3 Redis instances that we run in Elasticache:

- backend-redis
- logs-redis
- api-redis

Most applications use backend-redis, the logging cluster uses logs-redis (which should soon be replaced), and Rummager uses api-redis.

This was traditionally the case because Rummager lived in a different vDC to redis-1/redis-2, but this is no longer a concern in AWS.

### Decision

Update Rummager configuration so it uses backend-redis, and remove api-redis.

### Consequences

Everything relying on a single redis instance could potentially have impact if there is an issue with that Elasticache instance.

We will save money on not running multiple Elasticache instances.

## 30. Change in architecture to Asset Master

Date: 2017-09-15

### Status

Accepted

### Context

Traditionally we built an "asset-master-1" instance with a large disk, and exported that disk as an NFS share.

The "backend", "whitehall-backend" and "asset-slave" instances all mounted this NFS share for the tasks they needed to do (uploading files for the backend machines, and making backups on the asset-slave machines).

In AWS, we have the option to use [Elastic File System (EFS)](https://aws.amazon.com/efs). This is an autoscaling filesystem so we do not have to manage disk space, and is independent to any instance. Each instance would have to mount this filesystem in the same way as NFS, but it is not managed by us.

### Decision

We will create an EFS resource and expose the mount using our internal Route 53 DNS. We will allow the required machines to mount the resource using Security Groups.

The backend and whitehall-backend instances will mount as usual, and the asset-master will also mount the disk like an external share.

The asset-master is required to mount because it moves files about the filesystem after running virus scans.

A decision has yet to be made on the role of the asset-slave, as we could potentially move these tasks onto the asset-master (pushing backups to an S3 bucket, for example).

### Consequences

No more disk management on the asset-master.

Architecture has changed so there may be further work related to how do we backups of attachments.

## 31. Security Groups in Terraform

Date: 2017-11-28

### Status

Pending

### Context

Each terraform `aws_security_group_rule` requires a name. We need these to be both unique and useful so we need to define a basic standard for them. We have a few basic patterns shown below:

Code: Rule 1: ⏎ `allow_${source-name}_from_${dest-name}_$service_(ingress|egress)` ⏎ Example: ⏎ allow_bastion-elb_from_bastion-asg_ssh_ingress ⏎ Rule 2: ⏎ allow_${source-name}_(ingress|egress)_${dest-name}_$service ⏎ Example: ⏎ allow_bastion-elb_ingress_bastion-asg_ssh ⏎ Rule 3: ⏎ ${source-name}_(ingress|egress)_${dest-name}_$service ⏎ Example: ⏎ monitoring2_ingress_webapps-elb_nrpe ⏎ Rule 4: ⏎ ${source-name}_$service_(ingress|egress)_${dest-name} ⏎ Example: ⏎ monitoring2_nrpe_ingress_webapps-elb

There are a few other guidelines that will be the same between rules. `$service` will be a named service, not just a port number. If the rule uses a protocol other than TCP we will add an additional `_$proto` to the end.

### Decision

We will use "rule 3" and change all the existing rule names to comply with it.

### Consequences

All our `aws_security_group_rule` terraform resources will match a consistent naming scheme.

If we've missed a use case we will have to redo this document and change the actual names again.

## 32. transfer artefact binary

Date: 2018-03-26

### Status

Accepted

### Context

We create binary artifacts for applications when we execute the **Deploy_App** Jenkins job. The binary file (artifact) gets stored in an AWS S3 bucket (For example **govuk-integration-artefact**). We need the binary file to deploy the application to the next environment. For example, we will use the binary file from **Integration** to deploy the application in the **Staging** environment.

### Decision

We decided to use a mechanism that is located outside the environments involved and pass the contents to the correct locations when the package becomes available.

![Transfer Mechanism](./0032-transfer-artefact-binary-img01.png?raw=true "Transfer Mechanism")

#### Example

We will use the **Integration** and **Staging** environments as examples.

- 1. We execute the **Deploy_Apps -> router** Jenkins job in the Integration environment.
- 2. A binary file is created in the **govuk-integration-artefact** AWS S3 bucket.
- 3. We have an AWS SNS Topic called **govuk-integration-artefact**.
- 4. We have an AWS S3 **govuk-integration-artefact** bucket event notification. This event sends a notification to the AWS SNS Topic when an **ObjectCreate** event is triggered.
- 5. The **Staging** environment has an AWS S3 bucket called **govuk-staging-artefact**.
- 6. We have an AWS SNS Subscription that subscribes to the **govuk-integration-artefact** AWS SNS Topic. This subscription will enable Staging to know when a new object gets created in the **govuk-integration-artefact** AWS S3 bucket.
- 7. We have an AWS Lambda function called **govuk-staging-artefact**. This function copies objects from the destination bucket to the target bucket. The trigger for the function is the AWS SNS Subscription.

### Consequences

This process requires a new object to be created at the source for the mechanism to be triggered and executed. This means that when we are initially building an environment, we will have to execute the relevant **Deploy_Apps** jobs at the source environment after the target environment is built, to get the artifacts.

## 3. Networking Outline

Date: 2018-09-26

### Status

Pending

### Context

This ADR in part supersedes [0003](0003-aws-networking-outline.md).

In [ADR 0003](0003-aws-networking-outline.md), we specified some IP address ranges for staging and production - ones that matched Carrenza as far as possible.

As part of the gradual migration of Staging and Production to AWS, we need to use a VPN to talk to Carrenza, so the chosen IP addresses conflict.

### Decision

The VPCs will be assigned the following IP ranges:

- Environment | IP Range
- Integration | 10.1.0.0/16
- Staging | 10.12.0.0/16
- Production | 10.13.0.0/16
- Test | 10.200.0.0/16

That is:

- Integration and Test do not change.
- Staging moves from 10.2.0.0/16 to 10.12.0.0/16.
- Production moves from 10.3.0.0/16 to 10.13.0.0/16.

### Consequences

We can now set up short-lived VPNs between Carrenza Staging and Production environments and AWS Staging and Production environments.

## 3. Bouncer Public Load Balancer Configuration

Date: 2018-10-22

### Status

Pending

### Context

Currently, Bouncer public load balancer accepts HTTPS request on port 443 and redirects the traffic to port 80 on the Bouncer servers.

There are a primary as well as a secondary SSL/TLS certificate attached to this HTTPS listener of the load balancer.

### Decision

The configuration of the Bouncer public load balancer was modified to:

- 1. Add a second listener to the load balancer so that HTTP request on port 80 can be served by the Bouncer servers. This functionality exists in the Carrenza environment and we aim to replicate this feature to maintain feature parity.

### Consequences

In order to implement the decision above, the following code changes were done:

- 1. the terraform [plan](../../../terraform/projects/infra-public-services/main.tf)

was changed so that the input to the `aws/lb` terraform module specifies a second listener `"HTTP:80"   = "HTTP:80"` in the listener map for the Bouncer public load balancer.

- 2. the `aws/lb` terraform module [here](../../../terraform/modules/aws/lb/main.tf) had

to be fixed so that SSL/TLS certificates and SSL policies are not added to a HTTP listener.

## 36. Performance-Platform-And-BackDrop-Architecture

Date: 2019-01-23

### Status

Proposed

### Context

We currently have dedicated performance-platform environments for both the staging and production GovUK environments. The performance-platform is made up of the following services:

For GovUK Staging, the entire performance-platform resides in the GovUK PaaS:

- Stagecraft
- Spotlight
- PP-Admin
- Backdrop database
- Backdrop Worker, Read & Write API

For GovUK Production:

- Stagecraft  (GovUK PaaS)
- Spotlight  (GovUK PaaS)
- PP-Admin  (GovUK PaaS)
- Backdrop database  (Carrenza performance-mongo cluster)
- Backdrop Worker, Read & Write API  (Carrenza api-1 & api-2 nodes)

The info-frontend is the only service within the GovUK environments that makes connections to the read and write backdrop APIs. Specifically the endpoint www.gov.uk/performance/data directs traffic to backdrop. It accesses those APIs through the following environment corresponding names:

- www.performance.service.gov.uk
- www.staging.performance.service.gov.uk

Those names will resolve to fastly, which will serve what is required if cached, if it is not cached it will update its cache by hitting the appropriate backdrop endpoints, which for staging would be in the PaaS and for production reside on the api-1 and api-2 instances.

![Performance Platform](./0036-performance-platform-and-backdrop-architecture-img01.png?raw=true "Performance Platform")

### Decision

We have outlined the current architecture of the performance environment here.

This ADR outlines the current architecture of the performance platform for both the GovUK Staging and Production environments. It must be noted that the context of the ADR has been written during a migration period where GovUK services are been moved from Carrenza to AWS. It is mainly a record for people to see how the performance platform fits together with the GovUK environments.

### Consequences

Currently staging and production performance-platforms are not similar which is not ideal. But the purpose of writting up this ADR was for information gathering as part of the GovUK AWS migration. It can also be confirmed that info-frontend service in AWS, which is due to be migrated is able to access the performancer-platform using fastly.

## 37. ALB Health Checks

Date: 2019-06-24

### Status

Accepted

### Context

On our platform, application instances receive traffic routed from a load balancer. Typically, an application instance runs Nginx with a server_name based Vhost per application. Each application Vhost proxies the requests to the local port where the application listens.

Load balancers use a health check to determine which instances to send traffic to. Health checks depend on the type of load balancer and protocol in use. Usually we are going to configure health checks using TCP+PORT (ELBs) or HTTP+PORT+Request_path+Response_code (ALB). For more information on health checks, have a look at the following links:

https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-healthchecks.html https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html

When we configure HTTP health checks, the load balancer sends a request without a Host header. In this case, Nginx processes that request in the default Vhost. These requests have been configured in the default Vhost to serve an `200 OK` response code, which indicates to the load balancer that the instance is healthy and ready to receive traffic. This presents a problem when we are starting or redeploying applications in that instance, because the application port will be unavailable for a period of time, and Nginx will serve 5xx responses. The load balancer still sees the health check responses as `200 OK`, so it continues sending traffic to that instance, even though the application is not ready to receive traffic.

The current ALB health check is rudimentary and does only test for the basic Nginx configuration being in place, rather than testing whether all apps are properly deployed.  If an instance is terminated, this causes its replacement to be added to the target group pool prematurely which causes elevated 5xx rates.

### Decision

When an instance is running more than one application, we are going to route traffic to the instance with an ALB. Each application has a dedicated target group, with a specific health check path, following the format `/_healthcheck_<app-name>`.

This health check path is configured in the default Vhost to proxy the request to the upstream application, and rewrites the request to match the application health check path that is also used in Icinga checks. This is configured in Puppet, in `govuk::app::config`, as the `health_check_path` parameter.

The ALB includes routing rules based on Host header, and redirects the traffic to the application target group when the Host header matches the value `<<app-name>.*`

### Consequences

If an application health check is broken or hasn't been deployed properly, the load balancer will see that target as unhealthy and won't send traffic to.

We are going to have more target groups in the platform, we need to monitor closely the number of healthy hosts detected per target group and make sure we alert is we detect problems.

## 38. Mongo Replacement by DocumentDB

Date: 2019-10-17

### Status

Approved

### Context

GOV.UK uses MongoDB as the backing database for a number of apps. In a generic GOV.UK environment, there are 5 MongoDB clusters: one for Licensify (a legacy service), one for performance monitoring, one for router and another per cloud provider (i.e. AWS and Carrenza) for all other apps (e.g. assets, imminence, maslow, content, publisher and short url manager).

One architectural strategy principle of TechOps is to make use as much as possible AWS managed services in order to reduce the burden on GOV.UK teams to manage Commercial off-the-shelf (COTS) functionality/services.

### Decision

The approaches taken for migrating from MongoDB to AWS DocumentDB are:

- 1. new apps that are being migrated from legacy cloud providers (e.g UKCloud and Carrenza) to AWS and use MongoDB should be evaluated for compatibility with AWS DocumentDB during the migration phase. Based on this evaluation, a decision should be made based on cost benefit whether a particular migrating app should be using DocumentDB or MongoDB.
- 2. there are some apps (e.g. content store and imminence) that have already been migrated to AWS and uses the MongoDB cluster there. These apps should be evaluated for compatibility with AWS DocumentDB and prioritised accordingly for migration to AWS DocumentDB.

### Consequences

While migrating to AWS DocumentDB, there are a few facts to be aware of:

- 1. AWS DocumentDB has been developed to be [compatible](https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html) with the open source MongoDB API 3.6. The version of MongoDB that GOV.UK uses is 3.2.7 for Licensify and 2.4.9 for the other apps.

In addition, we are aware that AWS DocumentDB does not support the null character in any string and you should amend any records that contain these before migrating to AWS DocumentDB.

- 2. AWS DocumentDB requires authentication using username and password. This is in contrast with the current GOV.UK MongoDB clusters that are protected based on IP only. Hence, the relevant GOV.UK apps should have the ability to retrieve authentication credentials from GOV.UK credential management system and authenticate with AWS DocumentDB. This may require some code changes in some instances.
- 3. AWS DocumentDB supports multiple users but with the important caveat that all users are effectively super users and have access to all databases of their DocumentDB cluster. More information is available [here](https://docs.aws.amazon.com/documentdb/latest/developerguide/security.managing-users.html).
- 4. If TLS is activated on the AWS DocumentDB cluster, the connecting GOV.UK app will have to include the AWS DocumentDB certificates in its TLS certificates store. It should be noted that these certificates are AWS ones and cannot be customised by the user. This means that no custom GOV.UK CNAME can be generated for the AWS DocumentDB cluster and GOV.UK apps will have to use the Fully Qualified Domain Name (FQDN) that AWS has allocated to the DocumentDB cluster. If the DocumentDB has to be re-created, a new FQDN will be provided by AWS and will have to be propagated in GOV.UK infrastructure.
- 5. If a database is migrated to AWS DocumentDB, the relevant database backup mechanism needs to be updated. The GOV.UK `govuk_env_sync` tool has been updated to support DocumentDB as a database type. It should be noted that in addition to configuring `govuk_env_sync` in the usual manner, the authentication credentials to access the DocumentDB will have to be provided.

## 39. Non-GOV.UK domain policy

Date: 2022-10-10

### Status

Accepted

### Definitions

This proposal uses the [RFC2119](https://www.ietf.org/rfc/rfc2119.txt) standard for definitions of MUST, MUST NOT and MAY.

Definitions:

- "Authenticated": through an authentication method such as Signon, through [basic access authentication](https://en.wikipedia.org/wiki/Basic_access_authentication), or similar
- "Non-GOV.UK domain": a domain that does not end in `gov.uk`, such as `govuk.digital` or `govuk-internal.digital`. Note that `assets.publishing.service.gov.uk` is considered a GOV.UK domain.

### Context

It is dangerous to have a Non-GOV.UK domain that is publicly routable, without any authentication layer, and which does either of the following:

- 1. Looks like a GOV.UK site
- 2. Plays any publicly detectable part in serving content to a GOV.UK site

In either case, the domain might be flagged as a phishing site by systems such as [Google's Safe Browsing](https://transparencyreport.google.com/safe-browsing/search) technology, which is used by browsers including (but not limited to) Chrome to automatically block requests to the site.

At best, this would be an inconvenience, perhaps making it difficult to access internal tooling. At worst, this could cause a major incident, making large parts of GOV.UK inaccessible.

### Proposal

Any web page that lives on a Non-GOV.UK domain, and that is designed to look like a page or service on GOV.UK, MUST either be Authenticated or Unavailable to the Public Internet.

Additionally, the serving of any GOV.UK web page or assets MUST NOT use a Non-GOV.UK domain in any publicly detectable part of the request. Some examples of things to avoid:

- 1. Using a Non-GOV.UK domain in the redirect chain for a GOV.UK page or asset.
- 1. Making requests to a Non-GOV.UK domain for 'metadata' associated with a GOV.UK page or asset, e.g. a request for a GOV.UK asset triggering a second request for a favicon from a Non-GOV.UK domain.

To be clear, a Non-GOV.UK domain MAY be used in serving GOV.UK pages or assets, provided the domain in question is not publicly detectable. For example, `govuk-internal.digital` MAY be used under the hood to process a request, provided the domain is not exposed to the browser at any point in the request.

### Consequences

A number of Signon domains are currently in violation of this proposal. They MUST either be made Authenticated, Unavailable to the Public Internet, or else moved to a GOV.UK domain.

- https://signon.integration.govuk.digital/
- https://signon.staging.govuk.digital/
- https://signon.production.govuk.digital/

We should consider what automated tests can be written to enforce this proposal GOV.UK-wide, e.g. in Smokey.

We should also consider the work involved and the merits of retiring any Non-GOV.UK domains.

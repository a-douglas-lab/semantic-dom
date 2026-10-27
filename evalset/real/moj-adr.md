# MOJ Cloud Platform Architecture Decision Records

## 0. Record Architecture Decisions

Date: 2019-05-01

### Status

✅ Accepted

### Context

During our work on the Cloud Platform, we will have to make architectural decisions about the platform and associated tools & processes.

When making decisions, we should record them somewhere for future reference, to help us remember why we made them, and to help teams working in related areas understand why we made them.

We should make our decisions public so that other teams can find them more easily, and because [making things open makes things better](https://www.gov.uk/guidance/government-design-principles#make-things-open-it-makes-things-better).

### Decision

We will use Architecture Decision Records, as described by Michael Nygard in [this article](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)

An architecture decision record is a short text file describing a single decision.

We will keep ADRs in this public repository under decisions/[number]-[title].md

We should use a lightweight text formatting language like Markdown.

ADRs will be numbered sequentially and monotonically. Numbers will not be reused.

If a decision is reversed, we will keep the old one around, but mark it as superseded. (It's still relevant to know that it was the decision, but is no longer the decision.)

We will use a format with just a few parts, so each document is easy to digest:

**Title** These documents have names that are short noun phrases. For example, "ADR 1: Record architectural decisions" or "ADR 9: Use Docker for deployment"

**Status** A decision may be "proposed" if it's still under discussion, or "accepted" once it is agreed. If a later ADR changes or reverses a decision, it may be marked as "deprecated" or "superseded" with a reference to its replacement.

**Context** This section describes the forces at play, including technological, political, social, and local to the service. These forces are probably in tension, and should be called out as such. The language in this section is value-neutral. It is simply describing facts.

**Decision** This section describes our response to these forces. It is stated in full sentences, with active voice. "We will ..."

**Consequences** This section describes the resulting context, after applying the decision. All consequences should be listed here, not just the "positive" ones. A particular decision may have positive, negative, and neutral consequences, but all of them affect the team and service in the future.

The whole document should be one or two pages long. We will write each ADR as if it is a conversation with a future person joining the team. This requires good writing style, with full sentences organised into paragraphs. Bullets are acceptable only for visual style, not as an excuse for writing sentence fragments.

[adr-tools](https://github.com/npryce/adr-tools) can help us work with our ADRs consistently.

We will link to these ADRs from other documentation where relevant.

### Consequences

One ADR describes one significant decision for the service. It should be something that has an effect on how the rest of the service will run.

Developers and service stakeholders (and anyone else who's interested) can see the ADRs, even as the team composition changes over time.

The motivation behind previous decisions is visible for everyone, present and future. Nobody is left scratching their heads to understand, "What were they thinking?" and the time to change old decisions will be clear from changes in the service's context.

Having a central place to record decisions which affect all of our work will make the sequence of decisions clear, and make it easier for us to refer back to decisions later on.

This repo holds Architecture Decision Records, for the cloud platform team. We will be using the architecture decision record to help keep a record of what approaches we are currently taking to our infrastructure and to help our future selves understand why those decisions were made. The approach is described by Michael Nygard in [this article](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

Everyone can see the ADRs, even as the team composition changes over time. This means motivation behind previous decisions is visible for everyone, present and future. Nobody is left scratching their heads to understand, "What were they thinking?" and the time to change old decisions will be clear from changes in the project's context.

## Use AWS hosted Elasticsearch

Date: 05/02/2018

### Status

✅ Accepted

### Context

The cloud platforms team self-host an Elasticsearch cluster with Kibana and Logstash (ELK). This cluster has suffered numerous outages (see [CPT-282](https://dsdmoj.atlassian.net/browse/CPT-282) and [CPT-152](https://dsdmoj.atlassian.net/browse/CPT-152) in Jira) that have been difficult to recover from.

Reasons behind this move were:

- Average of almost one week per month spent on debugging, fixing and reviving ELK
- Lengthy downtimes which made data recovery pointless
- Self hosted ELK stacks cost was significantly higher than AWS ElasticSearch solution
- Not working ELK cluster was also a blocker for product teams as they couldn't see any application logs

### Decision

Replace our self hosted ELK stack with the managed AWS Elasticsearch

### Consequences

- 1. Application logs were already shipped directly from the servers to AWS CloudWatch Logs ( thanks to works on Service Catalogue project )
- 2. We have created lambda function for shipping logs into newly created AWS ES cluster
- 3. We have created a script to set lambda function mentioned above as a target for logs from AWS CloudWatch Logs ( script@opstools )
- 4. We have deleted the ELK stacks from all environments
- 5. We have modified Sensu alerting to use new ES cluster
- 5. Cluster healthchecks set up via Cloudwatch to ensure reliability.

Product teams have confirmed their application logs being shipped and searchable in new ELK cluster with as of now - zero downtime and maintenance from Cloud Platforms side.

We don't have any admin power over the cluster, unable to install either kibana plugins or change ES connectivity settings.

## Use GitHub for architecture decision log

Date: 26/03/2018

### Status

✅ Accepted

### Context

The cloud platforms team has had a number of discussions about where to hold documentation. We have tried using confluence for technical documentation but it has largely gone stale through lack of updates.

For the development of the new platform we want to keep _technical_ documentation close to the code that implements that documentation. An example of this is the [kubernetes investigations](https://github.com/ministryofjustice/kubernetes-investigations) repo which holds our experiments into the use of kubernetes.

Putting technical documentation in GitHub has additional benefits:

- Using pull requests gives us a clear review and approval process
- It is part of the same workflow as other activities that we do on a day to day basis (e.g. writing code)
- The information can be held in the open and viewed by anyone

### Decision

- 1. Our architecture decision log for the new cloud platform will be held in GitHub

### Consequences

Our existing architecture decisions will need to be migrated from Confluence (see this [pull request](https://github.com/ministryofjustice/cloud-platform/pull/1)).

## Use Concourse CI

Date: 28/03/2018

### Status

✅ Accepted

### Context

The cloud platforms team currently use a self-host Jenkins server for CI/CD pipeline. This solution is not cloud native. There is a large amount of custom configuration which has equated to a vast amount of user request tickets and an opaque service which would be very difficult to recover [CPT-364](https://dsdmoj.atlassian.net/browse/CPT-364)  There is also a reoccurring issue which has caused a number of outages [CPT-384](https://dsdmoj.atlassian.net/browse/CPT-384).

Reasons behind this move were:

- Average of almost one week per month spent on debugging, fixing and reviving jenkins
- Unnecessary downtimes
- With the move to Kubernetes a cloud native CI/CD solution is needed, all jobs are written as code
- Non working jenkins was a blocker for product teams

### Decision

Replace self hosted Jenkins with self hosted Concourse CI pipeline

### Consequences

- 1. Spike into deploying Concourse CI into AWS or Kubernetes [CPT-486](https://dsdmoj.atlassian.net/browse/CPT-486)
- 2. Decision made to deploy to Kubernetes [CPT-488](https://dsdmoj.atlassian.net/browse/CPT-488)
- 3. Automate deployment of concourse using Terraform and Helm
- 4. WIP

~~Product teams have confirmed their success builds and deploys. zero downtime and minimal maintenance from Cloud Platforms side.~~

## Use kubernetes for running containerised applications

Date: 10/04/18

### Status

✅ Accepted

### Context

MOJ Digital's approach to infrastructure management and ownership has evolved over time, and has led to the following outcomes:

- Unclear boundaries on ownership and responsibilities between service teams and the cloud platforms team
- Significant variation in deployment, monitoring and lifecycle management across products
- Inefficient use of AWS resources due to the use of virtual machine-centric architecture, despite our standardisation on Docker containers

The last few years has seen the advent of several products specifically focused on the problem of running and managing containers in production:

- Kubernetes
- Mesos / Mesosphere / DC/OS
- Docker Swarm
- AWS ECS
- CloudFoundry

Given the technology landscape within MOJ, we require a container management platform that can support a wide range of applications, from "modern" cloud-native 12-factor applications through to "legacy" stateful monolithic applications, potentially encompassing both Linux- and Windows-based applications; this removes CloudFoundry from consideration, given its focus on modern 12-factor applications and reliance on buildpacks to support particular runtimes.

From the remaining list of major container platforms, Kubernetes is the clear market leader:

- Rapid industry adoption during 2017 establishing it as the emerging defacto industry standard
- Managed Kubernetes services from all major cloud vendors
- Broad ecosystem of supporting tools and technologies
- Increasing support for Kubernetes as a deployment target for commercial and open-source software projects

There is also precedent for Kubernetes use within MOJ, as the Analytical Platform team has been building on top of Kubernetes for around 18 months.

### Decision

Use Kubernetes as the container management component and core technology for our new hosting platform.

### Consequences

- 1. Several technical spikes looking at Kubernetes itself and associated components - logging, monitoring, application deployment, etc.
- 2. Requirement to use an identity broker for Kubernetes user authentication, given the decision to use Github as an identity provider and the lack of a common auth protocol between Kubernetes and Github

## Monitoring/Alerting of ECR Image Counts

Date: 04/07/2019

### Status

✅ Accepted

### Context

We use ECR as the Docker container registry that makes it easy for users to store, manage, and deploy Docker container images. Due to some applications having a constant rate of images being pushed to their ECR repo, we found that the AWS limit of 1000 images was being hit by some teams. To avoid this we had implemented a lifecycle policy of *100 images* per ECR repo. ECR repositories created for use in the Cloud Platform will have this default lifecycle policy applied.

As lifecycle policy will only keep 100 most recent versions of an image and silently delete images, application users raised an [issue][user-issue] on imposing any limit on number of images is potentially dangerous, unless teams have their own clean-up mechanism.

### Decision

After discussing with application teams and consideration of possible options, the decision has been made to remove the lifecycle policy altogether, but adding monitoring and alerting such that we can take action before an ECR runs out of space.

As it is to do with metrics & alerts, since prometheus is our monitoring solution we decided to use prometheus for metrics & alerts.

### Consequences

- We are gathering metrics about the number of ECRs we have, and the number of images in each of them
- We have an 'amber' alert when any ECR contains more than 500 images
- We have a 'red' alert when any ECR contains more than 800 images
- We have an 'amber' alert when the number of ECRs rises above 500
- We have a 'red' alert when the number of ECRs rises above 800
- When alerts are trigerred for Image count, Inform relavent service teams to manage their repositories by cleaning up some old images.
- When alerts are trigerred for ECR count, raise a request for AWS to increase the count of repositories.

[user-issue]: https://github.com/ministryofjustice/cloud-platform/issues/839

## Use GitHub as our identity provider

Date 09/04/2018

### Status

✅ Accepted

### Context

As part of our [planning principles](https://docs.google.com/document/d/1kHaghp-68ooK-NwxozYkScGZThYJVrdOGWf4_K8Wo6s/edit) we highlighted "Building in access control" as a key principle for planning our building our new cloud platform.

Making this work for the new cloud platform means implementing ways that our users &mdash; mainly developers &mdash; can access the various bits of the new infrastructure. This is likely to include access to Kubernetes (CLI and API), AWS (things like S3, RDS), GitHub, and any tooling we put on top of Kubernetes that users will access as part of running their apps (e.g. ELK, [Prometheus](https://github.com/ministryofjustice/cloud-platform/blob/main/architecture-decision-record/026-Managed-Prometheus.md#choice-of-prometheus), [Concourse](https://github.com/ministryofjustice/cloud-platform/blob/main/architecture-decision-record/003-Use-Concourse-CI.md)).

At the current time there is no consistent access policy for tooling. We use a mixture of the Google domain, GitHub and AWS accounts to access and manage the various parts of our infrastructure. This makes it hard for users to make sure that they have the correct permissions to do what they need to do, resulting in lots of requests for permissions. It also makes it harder to manage the user lifecycle (adding, removing, updating user permissions) and to track exactly who has access to what.

We are proposing that we aim for a "single sign on" approach where users can use a single logon to access different resources. For this we will need a directory where we can store users and their permissions, including what teams they belong to and what roles they have.

The current most complete source of this information for people who will be the first users of the cloud platform is GitHub. So our proposal is to use GitHub as our initial user directory - authentication for the new services that we are building will be through GitHub.

### Decision

We will use GitHub as the identify provider for the cloud platform.

We will design and build the new cloud platform with the assumption that users will login to all components using a single GitHub id.

### Consequences

We will define users and groups in GitHub and use GitHub's integration tools to provide access to other tools that require authentication.

When adding new functionality or tooling to the platform we will design for using GitHub for authentication and authorisation. We will prefer tooling that integrates with GitHub directly, or has support for standards-compliant OIDC authentication (or SAML if that is not available) as Auth0 allows us to use Github identities as a generic authN/authZ source using those protocols. We will assess other solutions based on their ease of integration with GitHub.

## Use ECR As Container Registry

Date: 06/04/2018

### Status

✅ Accepted

### Context

The cloud platforms team currently use Docker Registry for storage of docker images. This solution is self-hosted, needs regular patching, and occasionally has downtime.

Example of an issue [CPT-274](https://dsdmoj.atlassian.net/browse/CPT-274).

We want to update the container registry to avoid some of the problems we have been seeing with it. The container registry will also be a key part of our new [Kubernetes based infrastructure](https://github.com/ministryofjustice/cloud-platform/blob/master/architecture-decision-record/004-use-kubernetes-for-container-management.md).

The criteria for selecting a new solution included:

- Finding a solution that would work with well GitHub based identity which is one of our [major architectural choices](https://github.com/ministryofjustice/cloud-platform/blob/master/architecture-decision-record/006-Use-github-as-user-directory.md)
- Decreasing the amount of day to day ops work, perhaps by using a managed service
- Good value for money
- Preference for open source tooling
- Can or is able to run addons i.e. security scanners
- We can make images that we host public by default

From this process we tentatively chose ECR. Unfortunately none of the SaaS registries in common use support Github authentication, but as ECR uses IAM for authentication, and IAM supports federated identity with Github via Auth0, it will in theory be possible to define ECR access policies that reference Github teams and roles.

### Decision

We will replace our self hosted Docker Registry to managed Elastic Container Registry (ECR).

### Consequences

We will go forward with implementing ECR as the container registry that we use. Our first aim will be to set this up as part of the [new build pipeline]().

@Kerin has done some proof of concept work on defining ECR access policies that reference Github teams and roles but we need to establish how we will map GitHub IDs to IAM roles we need to push and pull images before this decision is fully validated.

Following that we will replace the existing container registry with ECR.

### Notes

Some of the work that went into this decision:

- 1. Spike into what container registry service to use [CPT-479](https://dsdmoj.atlassian.net/browse/CPT-479). Nexus (self hosted), Artifactory (SaaS), ECR (managed)
- 2. Establish how concourse will push to the ECR container registry [CPT-511](https://dsdmoj.atlassian.net/browse/CPT-511)
- 3. Establish how concourse will push to the ~Nexus~ or Artifactory container registry [CPT-512](https://dsdmoj.atlassian.net/browse/CPT-512)
- 4. Decision made to use ECR [CPT-479](https://dsdmoj.atlassian.net/browse/CPT-479)

## Support Deployments from Third Party CI

Date: 03/05/2018

### Status

✅ Accepted

### Context

The cloud platforms team [is transitioning to Concourse CI](003-Use-Concourse-CI.md) internally. Product teams should also be able to use it, however, given that:

- Switching to Concourse CI would require familiarity with how it works and incur additional overhead
- We have not yet developed a streamlined approach to deployments through Concourse CI in order to confidently and properly offer support
- Product teams already use third party CI systems

We think it would be good as a starting point to make it easy for teams to deploy directly from the third party CI systems that teams are already using, rather than requiring the deployments to be implemented in Concourse CI.

### Decision

We will support deploying applications to the Cloud Platform from third party CI systems and will offer documentation on how to do so, at least for the most commonly used CI systems.

### Consequences

- 1. Cloud Platform adoption will be easier and quicker for product teams, since the required changes in their pipelines will be few.
- 2. Product teams can still use Concourse CI, but do not depend on it to get their applications deployed.
- 3. The Cloud Platform team has time to design an alternative based on Concourse CI.

## Naming convention for clusters

Date: 05/06/2018

### Status

✅ Accepted

### Context

As we are building our new platform on Kubernetes we have already found the need to build quite a few clusters. These have been for a range of purposes including users, testing new ideas ("sandbox"), testing new functionality ("test"), deploying apps to them ("non-production").

As we are still learning we are finding that:

- 1. we need to continue building new clusters for different purposes and
- 2. we often need to test the cluster creation process
- 3. we want to differentiate between clusters that have users on them and those that are for internal testing purposes
- 4. we do not want to differentiate cluster by function (e.g. "perf-test", "sandbox") or status ("non-production").

To make this easier we propose having a naming scheme that makes it easy to understand whether users are on that cluster but makes no other assumptions about what it is used for.

### Decision

We will name all clusters with the following naming scheme:

- `live-{n}` for any cluster that have users on them, for instance `live-1`.
- `test-{n}` for any cluster that do not have users on them and are used by the cloud platform team only, for instance `test-2`.

We will number the clusters sequentially.

### Consequences

- 1. Any new clusters that are built use this naming scheme (the first one using it is `live-1`)
- 2. We delete the current clusters: `sandbox`, `test` and `non-production` and transition users and functions to new clusters (`non-production` to `live-0`, `sandbox` and `test` to a new cluster called `test-0`)
- 3. We keep a central record of:
- 1. The names of all clusters that we run
- 2. If it has a particular function, what each cluster is for

## Migrate from live-0 to live-1 Cluster

Date: 28/02/2019

### Status

✅ Accepted

### Context

Migrating from live-0 to live-1 cluster. The reason behind this is based on the need to move to a dedicated AWS account (moj-cp), which will be much easier to support, and the need to move away from the Ireland (EU) region to the London (UK) region as Cloud Platform requirement to host data in the UK, rather than in Europe.

### Decision

After some long consideration of possible options, the decision has been made to migrate from the live-0 cluster to the new live-1 cluster.

Since we only want to be running a single cluster, we will need to shut down live-0 as soon as it's no longer needed. Also services migrate from live-0 to live-1 sooner will avoid the complexities of running two parallel clusters.

### Consequences

Creation of the live-1 cluster, which includes a move to the moj-cp AWS account, move to the eu-west-2 region and below tasks performed in live-1 cluster.

- 1. In Live-1, Introduce Pod Security Policies, to tighten the security on production cluster.
- 2. Live-1 Kubernetes version bump to 1.11.8 using kops, this is for security and feature implementation. 1.11.8 is the latest version kops will allow. live-0 is using 1.10
- 3. Change tenant to justice-cloud-platform.
- 4. Change all references to the integration.dsd.io to cloud-platform.service.justice.gov.uk.
- 5. Change the kops store to the moj-cp AWS account under s3://cloud-platform-kops-state. All S3 buckets need to be moved over to the new account.
- 6. In live-1 Amend all region information to eu-west-2 (London).
- 7. Update EBS version to 3.3.10 and Encrypted EBS volumes
- 8. Create Elasticsearch cluster in new AWS account live and audit
- 9. Remove nginx-ingress-controllers and made nginx-ingress-acme default, create tls rules for all Cloud Platform applications
- 10. Add new kuberos image.
- 11. Move pipelines running in live0 concourse cluster to live1 concourse cluster.

## Introduce Open Policy Agent

Date: 07/06/2019

### Status

✅ Accepted

### Context

On the Cloud Platform, there is a need to implement various policies to safeguard our tenant applications and to enforce best practices.

Kubernetes offers various mechanisms that cover some of our needs (eg.: `ResourceQuotas` to prevent resource exhaustion and `PodSecurityPolicies` to enforce non-root containers) but there are other areas for which there is no builtin solution. However, kubernetes implements a Dynamic Admission Control API which introduces [admission webhooks][admission-control]. This API provides an easy way with which to expand on the existing admission controllers (built in the apiserver).

Our immediate need was to prevent users from reusing hostnames in `Ingresses`. Although our ingress controller prevents hijacking of hostnames, it does so silently and furthermore, this is not a documented behaviour. Therefore, we decided that the user should not be allowed to reuse hostnames already defined in other `Ingresses` and receive a useful error message if they try to do that.

### Decision

We explored a number of existing solutions in the open source community, as well as the possibility of implementing our own and we also discussed the issue with other organisations that use kubernetes before reaching a conclusion.

Eventually we decided to introduce the [Open Policy Agent][open-policy-agent]:

- It is a generic framework for building and enforcing policies (whereas most other existing implementations were designed around specific problems)
- The policies are defined in a declarative, high-level language
- It is designed for cloud-native environments
- It provides a kubernetes integration
- It provides a way by which to unit test the policies
- The project is adopted by CNCF

Although the project is still in alpha and very likely to change in the near future, we decided that it is stable enough for our needs and worth adopting even at these early stages, since the benefits outweigh the cost.

### Consequences

By building the foundation, we have introduced a solid framework on which to build policies for our multi-tenant platform and have solved our immediate need of protecting application hostnames.

The project seems to have gained significant velocity and as it evolves we will need to follow the development closely and adapt our implementation.

### Notes

The first policy we introduced solves the aforementioned issue with hostnames in `Ingresses` and can be found [here](https://github.com/ministryofjustice/cloud-platform-infrastructure/tree/907918c3022f581d4ebbae828e3b8200b6f067cd/terraform/cloud-platform-components/resources/opa/policies).

[admission-control]: https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/ [open-policy-agent]: https://openpolicyagent.org

## One cluster for dev/staging/prod

Date: 01/06/2019

### Status

✅ Accepted

**June 2020 Update** The CP team is now in the habit of spinning up a [test cluster](https://github.com/ministryofjustice/cloud-platform-infrastructure/pull/742) to develop and test each change to the platform, before it is deployed to the main cluster (live). So although the main cluster still has dev/staging namespaces for service teams, this work is confined to their namespaces, and there's little concern that they would disrupt other namespaces. These user dev/staging namespaces could simply be seen as benefiting from the high service level offered for the cluster, due to it hosting the production namespaces.

**May 2021 Update** We're looking to move on from this ADR decision, and have different clusters for non-prod namespaces - see [021-Multi-cluster](https://github.com/ministryofjustice/cloud-platform/blob/main/architecture-decision-record/021-Multi-cluster.md)

### Context

The Cloud Platform needs to host both citizen-facing, production services, and development environments for service teams to iterate on their code, or just set up sandboxes for experimentation and learning.

To support this, should we have separate clusters for production, development, and staging? Or, should we run a single cluster hosting all these different types of workload?

### Decision

After consideration of the pros and cons of each approach we went with one cluster, using namespaces to partition different workloads.

Some important reasons behind this move were:

- A single k8s cluster can be made powerful enough to run all of our workloads
- Managing a single cluster keeps our operational overhead and costs to a minimum.
- Namespaces and RBAC keep different workloads isolated from each other.
- It would be very hard to keep multiple clusters (dev/staging/prod) from becoming too different to be representative environments

To clarify the last point; to be useful, a development cluster must be as similar as possible to the production cluster. However, given multiple clusters, with different security and other constraints, some 'drift' is inevitable - e.g. the development cluster might be upgraded to a newer kubernetes version before staging and production, or it could have different connectivity into private networks, or different performance constraints from the production cluster.

Based on our past experience, these differences tend to increase over time, to the point where the development cluster is too far away from production to be representative. The extra work required to maintain multiple environments becomes wasted effort.

If namespace segregation is sufficient to isolate one production service from another, then it is enough to isolate a team's development environment from a production service.

If namespace segregation is not sufficient for this, then the whole cloud platform idea doesn't work.

### Consequences

Having a single cluster to maintain works well for us.

- Service teams know that their development environments accurately reflect the production environments they will eventually create
- There is no duplication of effort, maintaining multiple, slightly different clusters
- All services are managed centrally (e.g. ingress controller, centralised log collection via fluentd, centralised monitoring with Prometheus, cluster security policies)

## Use RSpec for our cluster tests

Date: 04/07/2019

### Status

✅ Accepted

### Context

We need to be able to test that the production cluster(s) and any test clusters we create behave the way we expect them to.

So, we need automated tests that exercise a cluster and confirm that the effect we get is the one we expected.

### Decision

We chose the ruby testing framework [rspec] for this.

Although there are some go-based testing frameworks for kubernetes, there are some problems with them, and some benefits to rspec:

- The kubernetes testing frameworks seem quite immature, with limited documentation, tooling and other resources such as examples
- There is limited go expertise in the team
- RSpec is a very mature framework, with a lot of tooling, documentation and support
- There is a lot of ruby/rspec experience in the wider organisation
- Ruby is our scripting language of choice, so rspec fits with that

### Consequences

We have translated our existing bash-based smoke tests into Rspec [here][smoke-tests].

We have a structure for adding more tests as we need them.

We will be adding automated tests to our cluster build and monitoring pipelines, to ensure they stay up to date.

[rspec]: https://rspec.info/ [smoke-tests]: https://github.com/ministryofjustice/cloud-platform-smoke-tests

## Why we build our own kubernetes cluster

Date: 01/08/2019

### Status

✅ Accepted

### Context

MoJ Cloud Platform team has decided to use [kubernetes for container management platform](https://github.com/ministryofjustice/cloud-platform/blob/master/architecture-decision-record/004-use-kubernetes-for-container-management.md) following the outcome of MOJ Digital's approach to infrastructure management. The team needed the below features for the infrastructure management:

- An universal authentication mechanism to manage users without depending on the cloud provider
- Able to customize the control plane of kubernetes for MOJ requirement on Pod security
- Able to integrate external tools easily
- Able to manage and configure the control plane for any custom changes

### Decision

There are several leading cloud providers who provide managed production-ready kubernetes cluster:

- Amazon Elastic Kubernetes Service (Amazon EKS)
- Azure Kubernetes Service (AKS)
- Google Kubernetes Engine (GKE)

We decided to host our cluster on AWS because our service team has good development experience working with AWS services. This made it easier for teams to migrate to the kubernetes platform

We decided to manage the kubernetes cluster ourselves rather than using EKS mainly for the below reasons:

- When the time MOJ needed to build the kubernetes, Amazon EKS was still in the Alpha stage and was not production ready. Also Amazon EKS require to use IAM for user authentication which will be an overhead for managing users of service teams
- Kubernetes(k8s) allows to authenticate using OIDC and therefore it was easy to manage the authentication externally using Auth0

### Consequences

- Extra management overhead

Despite the fact we are already running a production cluster we will continue to evaluate the managed solutions in the future.

## Keeping Terraform modules up to date

Date: 23/03/2020

### Status

✅ Accepted

### Context

We maintain a lot of [terraform modules] which teams use to manage AWS resources for their namespaces.

In the past, lettings different namespaces use different versions of terraform modules has caused problems because there has not always been a clear upgrade path from a module that is several versions old, to the latest version.

In these cases, it would have been easier to have upgraded every namespace when the significant change was made to the module, because at that point in time the relevant knowledge and understanding are fresh. Leaving it until later makes the whole process much more difficult.

### Decision

We decided to ensure that all namespaces are always using the latest version of every module.

### Consequences

- We have to upgrade the module version in every affected namespace whenever we release a new version of a terraform module

[terraform modules]: https://github.com/ministryofjustice/cloud-platform#terraform-modules

## Kibana is open to all service teams

Date: 24/03/2020

### Status

✅ Accepted

### Context

We want users of the cloud platform to be able to access Kibana so that they can see the logs for their applications in a central place. AWS Kibana does not provide easy ways for users to authenticate. We need to put a proxy in front of Kibana so that users can authenticate with Github and then be redirected to the [Kibana dashboard][kibana-webconsole] to access their logs.

### Decision

It has been decided to use a combination of Auth0 and an OIDC proxy app. The application is managed in the [cloud-platform-terraform-monitoring repo][kibana-proxy] and configured ministryofjustice GitHub organization users to access Kibana.

### Consequences

- Kibana can be accessed by any member of the ministryofjustice GitHub organization, which will provide access to logs for all teams. Information written to log files can be of a sensitive nature, so it is important for users to keep sensitive data out of the logs.

[kibana-proxy]: https://github.com/ministryofjustice/cloud-platform-terraform-monitoring/blob/main/templates/oauth2-proxy.yaml.tpl [kibana-webconsole]: https://kibana.cloud-platform.service.justice.gov.uk/_plugin/kibana [kibana-access-task]: https://github.com/ministryofjustice/cloud-platform/issues/286

## Variable names in YAML & Terraform files are in snake case

Date: 17/08/2020

### Status

🤔 Proposed

### Context

We have a lot of scripts, pipeline definitions, terraform files, yaml files and templates which need to define and use variables. We want a consistent convention for naming these so that, as we write code in multiple, inter-dependent repositories, we can be confident that the names we are using are correct.

### Decision

We will always use snake case (e.g. `foo_bar`) for variable names which appear in terraform/yaml files and templates.

### Consequences

We should end up with fewer errors arising from scripts in one repo expecting, e.g. `repo_name`, but a template in another repo defining `repo-name` instead.

## Dedicated Ingress Controllers for teams

Date: 02/09/2020

### Status

❌ Rejected (see [019](019-Shared-Ingress-Controllers.md))

### Context

The Cloud Platform was originally set up to have a single ingress controller to manage all ingresses in the cluster. So, every new ingress added a config block to one, large nginx config file, and all traffic to all services hosted on the Cloud Platform is routed through a single AWS load balancer.

Although this was both easy to manage, and saved us some money on load balancers (approx. $25/month per ingress), it has become unsustainable. We usually have 6 replicas of the ingress controller pod, and we have started to see instances of several of these pods crash-looping (usually because they have run out of shared memory, which cannot be increased in kubernetes. See [this issue] for more information).

We believe this is because the nginx config has become so large (over 100K lines), that sometimes pods fail to reload it when it is changed, or the pod is moved.

### Decision

We will create a separate AWS load balancer and ingress-controller for every namespace in the cluster. An "ingress class" annotation will cause traffic for a particular ingress to be routed through the appropriate AWS load balancer and ingress-controller. See our [module repository] for more details.

"System" ingresses (e.g. those used for concourse, grafana, etc.) will continue to use the default ingress-controller. There should only ever be a handful of these, compared with hundreds of team ingresses, so the load on the default ingress-controller should stay within acceptable limits.

### Consequences

- The default ingress-controller will not crash (and take down all services in the cluster).
- The AWS hosting costs of the Cloud Platform will increase (because we will have to pay for more load balancers).
- The number of pods on the cluster will increase dramatically (two new pods per namespace, plus an additional pod if it's a production namespace).
- We may need more and/or larger worker nodes to run the additional pods, which will further increase our hosting costs.

[module repository]: https://github.com/ministryofjustice/cloud-platform-terraform-teams-ingress-controller [this issue]: https://github.com/kubernetes/kubernetes/issues/28272

## Shared Ingress Controllers for teams

Date: 09/09/2020

### Status

🤔 Proposed

### Context

The design proposed in [018](018-Dedicated-Ingress-Controllers.md) proved impossible to implement. Every ingress controller requires an AWS Network Load Balancer (NLB), and AWS have hard limits on the number of NLBs we can create per VPC and availability zone (AZ).

### Decision

We will:

- Disable mod-security on the default ingress-controller

This should enable this ingress-controller to comfortably handle thousands of ingresses.

- Create and manage a set of ingress controllers with mod-security enabled

Most, if not all, production services will want the protection of a web application firewall, and mod-security is the easiest to enable. We need to ensure that each ingress controller only handles as many mod-security-enabled ingresses as it can reliably cope with.

- Continue to have some dedicated ingress controllers

During our aborted migration to dedicated ingress controllers for every namespace, several ingress controllers were created for specific services. We will leave these in place to avoid additional disruption to these service teams.

### Consequences

- We will have to manage a pool of "mod-security-enabled" ingress controllers
- There will be additional, dedicated ingress controllers which, ideally, should not exist.
- We need to find out what is the maximum number of mod-security-enabled ingresses a single ingress controller can safely handle, and ensure we never exceed this.
- We may need to prevent teams from defining ingresses outside of the environments repository, since our current setup would enable teams to 'overload' a given ingress controller by using its ingress class in their ingress definitions. This could impact other services.

### UPDATE 2020-10-14

During the last kubernetes upgrade, we hit another AWS limit on the number of SecurityGroupRules (details in the [incident log]).

As part of the remediation, we removed all dedicated ingress controllers and migrated ingresses to the default controller, removing any modsecurity annotations.

[incident log]: https://runbooks.cloud-platform.service.justice.gov.uk/incidents/2020-10-06-intermittent-downtime-ingress-controllers.html

## 020. Environments and Pipeline

Date: 2021-02-26

(This ADR is written retrospectively, to explain decisions from 2017/2018)

### Status

🤔 Proposed

### Context

The key proposition of Cloud Platform is to do the "hosting" of services, and we choose [Kubernetes for container management](004-use-kubernetes-for-container-management.md).

In agreeing a good interface for service teams, there several concerns:

- Definitions - teams should be able to specify the workloads and infrastructure they want running.
- Control - teams should be able to use a default hosting configuration, getting things running as simply as with a PaaS. However teams should also have full control over their Kubernetes resources, including pod configuration, lifecycle, network connectivity, etc.
- Multi-tenancy - Service teams' workloads need isolation between their dev and prod environments, and from other service teams' workloads.

### Decisions

- 1. Teams are offered 'namespaces'. A namespace is the concept of an isolated environment for workloads/resources.
- 2. A CP namespace is implemented as a Kubernetes namespace and AWS resources (e.g. RDS instance, S3 bucket).
- 3. Isolation in Kubernetes namespaces is implemented using RBAC and NetworkPolicy:
- RBAC - teams can only administer k8s resources in their own namespaces
- NetworkPolicy - containers can only receive traffic from its ingresses and other containers in the same namespace (implemented with a NetworkPolicy, which teams can edit if needed)
- 4. Isolation between AWS resources is achieved using access control.

Each ECR repo, or S3 bucket, RDS bucket is made accessible to an IAM User, and the team are provided access key credentials for it.

- 5. A user defines a namespace in files: YAML (Kubernetes) and Terraform (AWS resources).

The YAML includes by default: a Namespace and various default limits on resources, pods and networking.

For deploying a simple workload, teams can include a YAML Deployment etc, so that these get applied automatically by CP's pipeline. Alternatively teams get more control by managing app resources using their namespace credentials - see below.

The Terraform can specify any AWS resources like S3 buckets, RDS databases, Elasticache. Typically teams specify an ECR repo, so they have somewhere to deploy their images to.

- 6. The namespace definition is held in GitHub.

GitHub provides a mechanism for peer-review, automated checks and versioning.

Other options considered for configuring a namespace do not come with these advantages, for example:

- a console / web form, implemented as a custom web app (click ops)
- commands via a CLI or API

Namespace definitions are stored in the [environments repo](https://github.com/ministryofjustice/cloud-platform-environments)

- 7. Namespace changes are checked by both a bot and a human from the CP team

In Kubernetes, cluster-wide privileges are required to apply changes to a Kubernetes Namespace, as well as associated resources: LimitRange, NetworkPolicy and ServiceAccount. These privileges mean that the blast radius is large when applying changes.

In terms of AWS resources, for common ones like S3 and RDS we provide terraform modules - to abstract away detail and promote best practice (for example, setting default encryption for S3 buckets). However Terraform can specify a huge range of AWS resources, each with multitude options. There are likely ways that one team can disrupt or get access to other teams' AWS services, that we can't anticipate, which is a risk to manage.

To mitigate these concerns:

- [automated checks](https://github.com/ministryofjustice/cloud-platform-environments/tree/main/.github/workflows) are used to validate against common problems
- Human review (by an engineer on the CP team) is also required on PRs, to check against unanticipated problems
- 8. Pipeline to deploy namespace automatically.

The "deploy pipeline" is a CI/CD pipeline that applies teams' namespace definitions in the clusters and AWS account. It triggers when the reviewed PR is merged to master.

- 9. Teams have full control within their Kubernetes namespace

Users are given access to Kubernetes user credentials (kubecfg) with admin rights to their namespace. This gives them full control over their pods etc. They can deploy with 'kubectl apply' or Helm. They can debug problems with pod starting up, see logs etc.

Users are also invited to create a ServiceAccount (using their environment YAML), and provide the creds to their CI/CD, for deploying their app.

## 21. Multi-cluster

Date: 2021-05-11

### Status

⌛️ Superseded by [036. Multi-cluster](036-multi-cluster.md)

### What’s proposed

We host user apps across _more than one_ Kubernetes cluster. Apps could be moved between clusters without too much disruption. Each cluster _may_ be further isolated by placing them in separate VPCs or separate AWS accounts.

### Context

Service teams' apps currently run on [one Kubernetes cluster](https://github.com/ministryofjustice/cloud-platform/blob/main/architecture-decision-record/012-One-cluster-for-dev-staging-prod.md). That includes their dev/staging/prod environments - they are not split off. The key reasoning was:

- Strong isolation is already required between apps from different teams (via namespaces, network policies), so there is no difference for isolating environments
- Maintaining clusters for each environment is a cost in effort
- You risk the clusters diverging. So you might miss problems when testing on the dev/staging clusters, because they aren't the same as prod.

(We also have clusters for other purposes: a 'management' cluster for Cloud Platform team's CI/CD and ephemeral 'test' clusters for the Cloud Platform team to test changes to the cluster.)

However we have seen some problems with using one cluster, and advantages to moving to multi-cluster:

- Scaling limits
- Single point of failure
- Derisk upgrading of k8s
- Reduce blast radius for security
- Reduce blast radius of accidental deletion
- Pre-prod cluster
- Cattle not pets

#### Scaling limits

Multi-cluster helps us we encounter a scale limitation. For example, we've found ourselves unexpectantly hitting an AWS limit during k8s upgrade. In this situation we could off-load some apps to another cluster. It would be advantageous to put each cluster in its own AWS account, to avoid limits, which are imposed per-account.

#### Single point of failure

Running everything on a single cluster is a 'single point of failure', which is a growing concern as more services use CP. Multi-cluster would allow us to quickly move apps off a broken cluster to another cluster.

Several elements in the cluster are a single point of failure:

- ingress (incidents: [1](https://runbooks.cloud-platform.service.justice.gov.uk/incidents/2020-10-06-intermittent-downtime-ingress-controllers.html) [2](https://runbooks.cloud-platform.service.justice.gov.uk/incidents/2020-04-15-nginx-tls.html))
- external-dns
- cert manager
- kiam
- OPA ([incident](https://runbooks.cloud-platform.service.justice.gov.uk/incidents/2020-02-25.html))

#### Derisk upgrading of k8s

Once you start a Kubernetes version upgrade, rolling back becomes infeasible (incidents: [1](https://runbooks.cloud-platform.service.justice.gov.uk/incidents/index.html#q1-2020-january-march)).

With multi-cluster we could do a "blue-green" upgrade - spin up an cluster at the newer k8s version and then carefully move the apps across to it.

#### Reduce blast radius for security

Taking a layered approach to security, extra isolation is beneficial. It resists lateral movement and minimizes the impact of a breach.

Isolation is added when you split the workloads across multiple clusters, even if they are in the same VPC. And further isolation is gained with separate VPCs or separate AWS accounts.

More sensitive apps may require this isolation.

Pre-prod environments are likely to often be running new code that has not have been through all the reviews, quality and security checks yet, so there may be a case for keeping these more isolated from environments with access to production data.

#### Reduce blast radius of accidental deletion

In the case of accidental deletion being run by a Cloud Platform team member, the ability to run administrative commands on only one cluster at a time would reduce the impact of this event, such as [this incident](https://runbooks.cloud-platform.service.justice.gov.uk/incidents/2020-09-21-some-cloud-platform-components-destroyed.html). Disaster Recovery procedures are in [good shape now](https://runbooks.cloud-platform.service.justice.gov.uk/disaster-recovery-scenarios.html#cloud-platform-disaster-recovery-scenarios), but it's worth minimizing blast radius all the same.

#### Pre-prod cluster

Test clusters are used by the Cloud Platform team to test changes. These are made as realistic as possible, inheriting IaC and config from the main cluster, and the availability of test apps. However test clusters have a different lifecycle, don't run realistic loads and don't have traffic / loads. Ideally we test CP changes in the most realistic way possible, before changes are deployed to the part of the platform where production workloads are running.

Multi-cluster will allow us to put pre-prod environments on a separate cluster to prod environments. Then changes to the platform, once tested on a test cluster, we can roll them out to the pre-prod cluster, as a more realistic test, ahead of rolling out to the prod clusters. This is particularly beneficial for more fundamental changes like upgrading k8s, and single points of failure such as ingress or OPA.

#### Challenge of moving apps

If we were to create a fresh cluster, and an app is moved onto it, then there are a lot of impacts:

- **Kubecfg** - a fresh cluster will have a fresh kubernetes key, which invalidates everyone's kubecfg. This means that service teams will need to obtain a fresh token and add it to their app's CI/CD config and every dev will need to refresh their command-line kubecfg for running kubectl.
- **IP Addresses** - unless the load balancer instance and elastic IPs are reused, it'll have fresh IP addresses. This will particularly affect devices on mobile networks that accessing our CP-hosted apps, because they often cache the DNS longer than the TTL. And if CP-hosted apps access third party systems and have arranged for our egress IP to be allow-listed in their firewall, then they will not work until that's updated.

### Steps to achieve it

More ideas for steps towards this are here: https://docs.google.com/document/d/1-1dXD0a50MZiQUcm4fIIO1ySVQHA_D2-UMIti-oBVNc/edit#heading=h.4hza65nlnk7p

### Decision

TBD

## EKS

Date: 11/11/2024

### Status

✅ Accepted

### What’s proposed

Use Amazon EKS for running the main cluster, which hosts MOJ service teams' applications. This replaces usage of kOps.

### Reasoning

Benefits of EKS:

- a managed control plane (master nodes), reducing operational overhead compared to kOps, such as scaling the control plane nodes. And reduces risk to k8s API availability, if there was a sudden increase in k8s API traffic.
- [managed nodes](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html), further reducing operational overhead
- Kubernetes upgrades are smoother:
- kOps rolling upgrades have been problematic. e.g. during 1.18 to 1.19 upgrade kOps caused us to have to [work around a networking issue](https://docs.google.com/document/d/1HzmTk0IvuW1XsXmVJEsSOzB4jkiMpjwZWlUwIF7P9Gc/edit)
- CP team sees kOps upgrades as particularly stressful, and 3rd on our risk register
- it opens the door to using [ELB for ingress](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html). Being managed, it is seen as preferable to self-managed nginx, which requires upgrades, scaling etc.
- avoid security challenge of managing tokens that are exported with `kops export kubeconfig`

We already run the Manager cluster on EKS, and have gained a lot of insight and experience of using it.

### EKS configuration decisions

#### Auth

**Chosen:** OIDC, with Auth0 as broker and GitHub as Identity Provider

Developers in service teams need to use the k8s auth, and GitHub continues to be the most common SSO amongst them with good tie-in to JML processes - see [ADR 6 Use GitHub as our identity provider](006-Use-github-as-user-directory.md)

Auth0 is useful as a broker, for a couple of important [rules that it runs at login time](https://github.com/ministryofjustice/cloud-platform-terraform-global-resources-auth0):

- it ensures that the user is in the ministryofjustice GitHub organization, so only staff can get a kubeconfig and login to CP websites like Grafana
- it inserts the user's GitHub teams into the OIDC ID token as claims. These are used by k8s RBAC to authorize the user for the correct namespaces

Future options:

- Azure AD SSO is growing in MOJ - there's a case for switching to that, if it is adopted amongst our users
- IAM auth has the benefit of immediately revoking access. Maybe we could use federated login with GitHub? (But would that give only temporary kubecfg?) Or sync the GitHub team info to IAM?

**Status**: Completed 2/6/21 [#2854](https://github.com/ministryofjustice/cloud-platform/issues/2854)

#### Auth credential issuer

**Chosen:** Cloud Platform Kuberos

We've long used Kuberos for issuing kubecfg credentials to users. The [original version of Kuberos](https://github.com/negz/kuberos) is unmaintained, but it's pretty simple, so we have updated the dependencies in: https://github.com/ministryofjustice/cloud-platform-kuberos/ and will maintain our fork.

Other options considered:

- [Gangway](https://github.com/heptiolabs/gangway) - similar to Kuberos, it has not had releases for 2 years (v3.2.0)
- [kubelogin](https://github.com/int128/kubelogin)
- CP team would have to distribute the client secret to all users. It seems odd to go to the trouble of securely sharing that secret, to overcome the perceived difficulty of issuing kubecfg credentials.
- Requires all of our users to install the software, rather than doing it server-side centrally
- [kubehook](https://github.com/negz/kubehook) - not compatible with EKS - doesn't support web hook authn
- [dex](https://github.com/dexidp/dex) - doesn't have a web front-end for issuing creds - it is more of an OIDC broker

**Status:** Completed 24/6/21 [#1254](https://github.com/ministryofjustice/cloud-platform/issues/2945)

#### Authorization

**Chosen:** existing RBAC configuration

We'll continue to use our existing RBAC configuration from the previous cluster.

**Status**: Completed 2/6/21 [#2854](https://github.com/ministryofjustice/cloud-platform/issues/2854)

#### Node management

**Chosen:** Managed node groups, with future experimenting with Fargate

Options:

- Self-managed nodes
- Managed node groups - automates various aspects of the node lifecycle, including creating the EC2s, the auto scaling group, registration of nodes with kubernetes and recycling nodes
- Fargate nodes - fully automated nodes, the least to manage. Benefits from more isolation between pods and automatic scaling. Doesn't support daemonsets.

We aim to take advantage of as much automation as possible, to minimize the team's operational overhead and risk. Initially we'll use managed node groups, before looking at Fargate for workloads.

**Status**: Completed 2/6/21 [#2854](https://github.com/ministryofjustice/cloud-platform/issues/2854)

##### Future Fargate considerations

_Pod limits_ - there is a quota limit of [500 Fargate pods per region per AWS Account](https://aws.amazon.com/about-aws/whats-new/2020/09/aws-fargate-increases-default-resource-count-service-quotas/) which could be an issue, considering we currently run ~2000 pods. We can request AWS raise the limit - not currently sure what scope there is. With Multi-cluster stage 5, the separation of loads into different AWS accounts will settle this issue.

_Daemonset functionality_ - needs replacement:

- fluent-bit - currently used for log shipping to ElasticSearch. AWS provides a managed version of [Fluent Bit on Fargate](https://aws.amazon.com/blogs/containers/fluent-bit-for-amazon-eks-on-aws-fargate-is-here/) which can be configured to ship logs to ElasticSearch.
- prometheus-node-exporter - currently used to export node metrics to prometheus. In Fargate the node itself is managed by AWS and therefore hidden. However we can [collect some useful metrics about pods running in Fargate from scraping cAdvisor](https://aws.amazon.com/blogs/containers/monitoring-amazon-eks-on-aws-fargate-using-prometheus-and-grafana/), including on CPU, memory, disk and network

_No EBS support_ - Prometheus will run still in a managed node group. Likely other workloads too to consider.

_how people check the status of their deployments_ - to be investigated

_ingress can't be nginx? - just the load balancer in front_ - to be investigated

If we don't use Fargate then we should take advantage of Spot instances for reduced costs. However Fargate is the priority, because the main driver here is engineer time, not EC2 cost.

#### Node groups

**Chosen:** A main node group for majority workloads, and a prometheus node group.

We'll minimize the number of node groups, to minimize the operation overhead.

For Prometheus, we continue our design from our previous cluster, where we have a separate node group of larger nodes, dedicated to Prometheus pods. This is because Prometheus is resource hungry for memory and disk IOPS. We will have two large nodes, in a single availability zone, so they can both access the EBS volume that stores metrics data.

Further node groups may be valueable for using Spot or Fargate nodes, as we explore them in the future.

**Status:** Completed - Prometheus node group 27/8/21 [#2979](https://github.com/ministryofjustice/cloud-platform/issues/2979)

#### Node instance types

**Chosen:** r5.xlarge, r5.4xlarge, r5a.xlarge - for the main node group

**Chosen:** IP Prefixes [configured](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-prefix-eni.html) in the image

In choosing instance types, our past experience has been that memory tends to be the limiting factor, so we have gone for the memory optimized range of instance types - 'r'. r5a is the latest, and most cost efficient, in that range, without going for ARM processors (see consideration below). However r5.xlarge is what we use on the current cluster, so we'll stick with that for now and move to r5a.xlarge after the migration.

The choice of AWS CNI networking in the new cluster, initially added a constraint on the number of pods per node, due to limitations on numbers of ENIs / IP addresses. However AWS has now released [IP prefixes](https://aws.amazon.com/about-aws/whats-new/2021/07/amazon-virtual-private-cloud-vpc-customers-can-assign-ip-prefixes-ec2-instances/), giving higher pod density per node, which enables us to avoid this limit. Support is added in [AWS CNI 1.9.0](https://github.com/aws/amazon-vpc-cni-k8s/releases/tag/v1.9.0) and it requires instances to be "nitro"-based, which the r5 range is, but not r4.

So the primary choice is:

- r5.xlarge - 4 vCPUs, 32GB memory

With fallbacks (should the cloud provider run out of these in the AZ):

- r5.2xlarge - 8 vCPUs, 64GB memory
- r5a.xlarge - 4 vCPUs, 32GB memory

In the future we might consider the ARM processor ranges, but we'd need to consider the added complexity of cross-compiled container images.

**Chosen:** r5.2xlarge, r4.2xlarge - for the Prometheus node group

The existing cluster uses r5.2xlarge, so we'll continue with that, and add some fall-backs:

- r5.2xlarge - memory optimized range - 8 cores 64 GB
- r4.2xlarge - memory optimized range - 8 cores 61 GB

**Status:**

- 1/9/21 r5.xlarge is in place for main node group - a temporarily a high number of instances
- IP prefixes is in the backlog [#3086](https://github.com/ministryofjustice/cloud-platform/issues/3086)

#### Pod networking (CNI)

**Chosen:** AWS VPC networking (CNI)

Link: https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html

AWS's CNI is used for the pod networking (IPAM, CNI and Routing). Each pod is given an ENI and IP address from the underlying VPC (rather than an overlay network). Pod traffic is routed between nodes using the native VPC.

Advantages of AWS's CNI:

- it is the default with EKS, native to AWS, is fully supported by AWS - low management overhead
- offers good network performance

The concern with AWS's CNI would be that it uses an IP address for every pod, and there is a [limit per node](https://github.com/awslabs/amazon-eks-ami/blob/main/nodeadm/internal/kubelet/eni-max-pods.txt), depending on the EC2 instance type and the number of ENIs it supports. The calculations in [Node Instance Types](#node-instance-types) show that with a change of instance type, the cost of the cluster increases by 17% or $8k, which is acceptable - likely less than the engineering cost of maintaining and supporting full Calico networking and custom node image.

The alternative considered was [Calico networking](https://docs.projectcalico.org/getting-started/kubernetes/managed-public-cloud/eks#install-eks-with-calico-networking). This has the advantage of not needing an IP address per pod, and associated instance limit. And it is open source. However:

- We wouldn't have any support from the cloud provider if there were networking issues.
- We have to maintain a customized image with Calico installed. It's likely that changes to EKS over time will frequently cause breakages with this networking setup.
- Installation requires recycling the nodes, which is not a good fit with declarative config.

**Status**: Completed 2/6/21 [#2854](https://github.com/ministryofjustice/cloud-platform/issues/2854)

#### Node image

**Chosen:** Amazon EKS optimized AMIs

Link: https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html

These EKS AMIs are the default and therefore lowest maintenance. We can't see a reason not to use them. (If we needed changes, then a launch config would give us flexibility.)

**Status**: Completed 2/6/21 [#2854](https://github.com/ministryofjustice/cloud-platform/issues/2854)

#### Cluster scaling

**Chosen:** Manual cluster scaling, with future consideration of auto-scaling

Initially we will continue manually scaling up/down the nodes manually, as we did on the kops cluster. This has proven fine, since the workload changes only slowly. And we have alerts set-up to warn when capacity is low, to prompt the team to scale the cluster.

Cluster auto-scaling should be considered soon though. This is to embrace one of the cloud's key advantages - to scale up/down swiftly, for good efficiency. For example, usage of the hosted sites is much lower at night, so we should aim to get our workloads to scale down automatically, and our cluster to follow suit. In addition, tenants' non-production environments do not need to run at all at night.

Considerations for auto-scaler:

- we need to maintain spare capacity, so that workloads that scale up don't have to wait for nodes to start-up, which can take about 7 minutes. This may require some tuning.
- tenants should be encouraged to auto-scale their pods effectively (e.g. using the Horizontal pod autoscaler), to capitalize on cluster auto-scaling
- scaling down non-prod namespaces will need agreement from service teams

**Status:**

- 18/8/21 Manual scaling in place [#3033](https://github.com/ministryofjustice/cloud-platform/issues/3033)
- 23/9/21 Auto-scaler is still desired

#### Network policy enforcement

**Chosen:** Calico network policy enforcement (i.e. just for policy, not the full blown Calico networking)

Link: https://docs.projectcalico.org/getting-started/kubernetes/managed-public-cloud/eks#install-eks-with-amazon-vpc-networking

This implements the Kubernetes Network Policy API, needed to isolate tenants. It is [recommended by EKS](https://docs.aws.amazon.com/eks/latest/userguide/calico.html). The CP team used it in the previous live-1 cluster, and are familiar with it.

CP's namespaces have a [default NetworkPolicy](https://github.com/ministryofjustice/cloud-platform-environments/blob/main/namespace-resources-cli-template/04-networkpolicy.yaml) that only allows incoming requests from pods in the same namespace and ingress-controller namespace, not other tenants' namespaces.

An alternative is [AWS Security Groups](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html). Creating a 'SecurityGroupPolicy' resource for a namespace would attach a security group, allowing us to specify the inbound and outbound network traffic. The [advantage](https://github.com/aws/containers-roadmap/issues/177) over a similar NetworkPolicy, is that the Security Group can specify AWS resources like RDS instances. So it would be a network restriction, in addition to the auth restriction (CP's RDS instances are currently [network accessible across the VPC](https://user-guide.cloud-platform.service.justice.gov.uk/documentation/other-topics/rds-external-access.html#accessing-your-rds-database)). We should explore this in the future for defence in depth.

**Status**: Completed 7/6/21 - AWS Calico (network policy enforcement) installed [#2974](https://github.com/ministryofjustice/cloud-platform/issues/2974)

**Chosen:** Calico Typha

Install Typha for performance benefits. It caches requests made by Calico Felix to the k8s API.

#### Control plane logging

**Chosen:** enable all cluster logging

Link: https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html

Control plane logs can be enabled to log: k8s API, authentication, controller manager and scheduler

The logs go to CloudWatch. Maybe we need to export them elsewhere. Further discussion is covered in: [ADR 23 Logging](023-Logging.md)

**Status:** Completed 25/8/21 [#2860](https://github.com/ministryofjustice/cloud-platform/issues/2860)

#### Node terminal access

**Chosen:** AWS Systems Manager Session Manager; no bastion nodes

Links:

- https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/install-ssm-agent-on-amazon-eks-worker-nodes-by-using-kubernetes-daemonset.html
- https://github.com/aws/containers-roadmap/issues/593

AWS Systems Manager Session Manager benefits:

- easy to install - daemonset
- auth is via a team member's AWS creds, so it's tied into JML processes and access can be removed immediately if they leave the team, and 2FA is the norm
- terminal commands are logged - useful for audit purposes
- [it's an EKS best practice](https://aws.github.io/aws-eks-best-practices/security/docs/hosts/#minimize-access-to-worker-nodes)
- we can take advantage of other Systems Manager features in future, including diagnostic and compliance monitoring

To note:

- requires permissions `hostNetwork: true` and `privileged: true` so may need its own PSP
- it's no use if the node is failing to boot or join the cluster properly, but we can live with that - it's likely that it's the pods we want to characterize, not the node, because the node is managed

The traditional method of node access would be to SSH in via a bastion. This involves a shared ssh key, and shared credentials is not an acceptable security practice.

**Status**

Completed 2/9/21

- Implementation ticket: https://github.com/ministryofjustice/cloud-platform/issues/2962
- Runbook for usage: https://runbooks.cloud-platform.service.justice.gov.uk/eks-node-terminal-access.html

#### PodSecurityPolicies

**Chosen:** Default EKS PSP `eks.privileged` should be used only by `aws-node` pod

**Chosen:** Apply CP's existing `privileged` PSP only to the `kube-system` namespace and `restricted` PSP to the rest

EKS comes with PSP `eks.privileged` that allows anything. However, security best practice is to limit it, to ensure most pods aren't allowed to run as privileged or root. [EKS best practices says]: "we recommend that you scope the binding for privileged pods to service accounts within a particular namespace, e.g. kube-system, and limiting access to that namespace". In practice we found only `aws-node` pod needed it.

CP already has `privileged` and `restricted` PSPs which we can apply as on the existing cluster.

**Status:** completed 13/5/21 in [#1172](https://github.com/ministryofjustice/cloud-platform-infrastructure/pull/1172) and [#1174](https://github.com/ministryofjustice/cloud-platform-infrastructure/pull/1174)

##### PSP Deprecation

PSPs are [deprecated](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/) as of k8s 1.21 (April 2021) and will be removed 1.25 (due April 2022). This is because PSPs are considered a difficult way to specify policy. It's not clear what will replace them, but OPA Gatekeeper is a possibility. We will look to move from PSPs to whatever standard is selected in the KEP over coming months.

**Status**: 24/9/21 Outstanding. In backlog: [#2706](https://github.com/ministryofjustice/cloud-platform/issues/2706)

#### Apps' access to AWS roles

**Chosen:** IAM Roles for Service Accounts (IRSA), instead of kiam

**Status:** Completed 21/7/21 - kube2iam usage is migrated to IRSA [#3014](https://github.com/ministryofjustice/cloud-platform/issues/3014) and [#2944](https://github.com/ministryofjustice/cloud-platform/issues/2944). kube2iam is not running on new cluster at all.

**Chosen:** Block access to instance metadata's node role

**Status:** Completed 18/8/21 - Access to instance metadata is blocked [#2942](https://github.com/ministryofjustice/cloud-platform/issues/2942)

##### IRSA

Benefits of IRSA over kiam or kube2iam:

- kiam/kube2iam require running and managing a daemonset container.
- kiam/kube2iam require [powerful AWS credentials](https://github.com/jtblin/kube2iam#iam-roles), which allow EC2 boxes to assume any role. Appropriate configuration of kiam/kube2iam aims to provide containers with only a specific role. However there are security concerns with this approach:
- With kube2iam you have to remember to set a `--default-role` to use when annotation is not set on a pod.
- When a node boots, there may be a short window until kiam/kube2iam starts up, when there is no protection of the instance metadata. In comparison, IRSA injects the token into the pod, avoiding this concern.
- With kube2iam/kiam, an attacker able to get root on the node could access the credentials and therefore any AWS Role. In comparison, with IRSA a breach of k8s might only have bring access to the AWS Roles that are associated with k8s service roles.

##### Blocking access instance metadata

The EKS node needs various AWS permissions, and these are provided by the node role. To avoid pods using these permissions, we should block access. Implementation details are provided here: https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node. This has been achieved using a [GlobalNetworkPolicy](https://github.com/ministryofjustice/cloud-platform-infrastructure/pull/1262/files).

## 23 Logging

Date: 11/11/2024

### Status

✅ Accepted

### Context

> Cloud Platform's existing strategy for logs has been to **centralize** them in an ElasticSearch instance (Saas hosted by AWS OpenSearch).

As of November 2024, we have migrated the logging service over to AWS OpenSearch, with ElasticSearch due for retirement (pending some decisions and actions on how to manage existing data retention on that cluster). Service teams can use OpenSearch's [search and browse functionality](https://app-logs.cloud-platform.service.justice.gov.uk/_dashboards/app/home#/) for the purposes of debugging and resolving incidents. All pods' stdout get [shipped using Fluentbit](https://user-guide.cloud-platform.service.justice.gov.uk/documentation/logging-an-app/log-collection-and-storage.html#application-log-collection-and-storage) and ElasticSearch stored them for 30 days. The full lifecycle policy configuration for OpenSearch can be viewed [here](https://github.com/ministryofjustice/cloud-platform-infrastructure/blob/main/terraform/aws-accounts/cloud-platform-aws/account/resources/opensearch/ism-policy.json.tpl).

Concerns with existing ElasticSearch logging:

- ElasticSearch costs a lot to run - it uses a lot of memory (for lots of things, although it is disk first for the documents and indexes)
- CP team doesn't need the power of ElasticSearch very often - rather than use Kibana to look at logs, the CP team mostly uses `kubectl logs`
- Service teams have access to other teams' logs, which is a concern should personal information be inadvertantly logged
- Fluentd + AWS OpenSearch combination has no flexibility to parse/define the JSON structure of logs, so all our teams right now have to contend with grabbing the contents of a single log field and parsing it outside ES

With these concerns in mind, and the [migration to EKS](https://github.com/ministryofjustice/cloud-platform/blob/main/architecture-decision-record/022-EKS.md) meaning we'd need to reimplement log shipping, we reevaluate this strategy.

### User needs

Logs are used for several purposes, so it's worth considering them separately:

**Observing apps** - service teams need to see the logs from their apps and ingress, to be able to test new app features and debug issues (e.g. app crashes on start-up). They need to browse and search. A popular feature request is for structured logs, where each log line is a JSON object, with each field searchable in the log UI. Some others have asked about using them for dashboards.

**Observing the platform** - CP team need to see the logs from the k8s control plane, k8s components, pipeline and other platform services, from the past few days, to be able to test new platform features and debug issues.

**KPI dashboards** - CP team needs to monitor KPIs, which are machine-readable. It's likely that some of these KPIs will include counts of logged events, such as Auth0 log-ins. (KPIs will probably need to cover other things too, such as grafana monitoring, number of GitHub repos, cloud costs.)

**Security** - service teams, CP team and Security & Privacy team need to monitor and investigate attacks. To quickly react to threats, we need to be able to do a quick search across the platform's logs for an IP or URL pattern, rather than logs de-centralized. We work to provide the Security & Privacy to have this on MLAP (MOJ Logging Aggregation Platform), their centralized SIEM (Security Information and Event Management) platform. (SIEMs do threat detection, using constantly updated lists of threats, such as known bad actor IP addresses, hosts, OWASP URL patterns, etc.) For investigation, logs need retaining for 13 months. CP team needs to be involved when findings come in, to add knowledge of the system to the assessment.

### Design discussion

Rather than centralized logging in ES, we'll evaluate different logging solutions, to fit the varied needs identified.

**AWS services for logging** - with the cluster now in EKS, it wouldn't be too much of a leap to centralizing logs in CloudWatch and make use of the AWS managed tools. One one hand it's proprietary to AWS, so adds cost of switching away. But it might be preferable to the cost of running ES, and related tools like GuardDuty and Security Hub, with use across Modernization Platform, is attractive.

#### Observing apps\*\*

- Loki - seems a good fit. For occasional searches, a disk-based index seems more appropriate - higher latency than memory, but much lower cost to run. (In comparison, ES describes itself as primarily disk based indexes, but it _requires_ heavy use of memory.) Could setup an instance per team. Need to evaluate how we'd integrate it, and usability.
- CloudWatch Logs - possible and low operational overhead - needs further evaluation.
- Sentry - Some teams have beeing using Sentry for logs, but [Sentry says themself it is better suited to error management](https://sentry.io/vs/logging/), which is a narrower benefit than full logging.

#### Observing the platform

CloudWatch is where both EKS and AWS components send platform logs. There may be a driver (such as KPIs) that say we need to ship these to Elastic or Loki in the future. A CloudWatch retention policy can be set to match needs.

#### KPI dashboard

TBD

#### Security

- MLAP was designed for this, but it is stalled, so probably best to manage it ourselves.
- ElasticSearch does have open source plugins for SIEM scanning. And it offers quick searching needed during a live incident. Maybe we could reduce the amount of data we put in it. But fundamentally it is an expensive option, to get both live searching and long retention period.
- AWS-native solution using GuardDuty and CloudWatch Logs may provide something analogous.

### Next steps

21/1/22 DR suggests investigating centralizing logs in CloudWatch Logs

## 24. Use SSO for CP Team to access AWS Console

Date: 2021-03-31

### Status

🤔 Proposed

### Proposal

We will enable AWS Single Sign-On (SSO) log-in to Cloud Platform AWS accounts:

- GitHub will be the Identity Provider, meaning users enter their GitHub username/password/2FA during login
- Auth0 will be the broker
- AWS SSO will be configured to allow the `webops` GitHub team access to two administrative IAM Roles: for read-only access and read+write access

This login method will be used by the Cloud Platform team to access Cloud Platform's AWS account, with both console and command-line access.

This sign-in has a time-out, depending on the role:

- read-only role - 12 hours
- read+write role - 1 hour

This method of authentication replaces the team's existing:

- signing into the AWS Console using current methods:
- SAML login - using GitHub, Auth0 and AWS SAML Federation
- Console password and MFA (for people who SAML didn't work), for their IAM User
- access key for their IAM User

We'll transition CP team to use SSO, switch off SAML auth and delete their IAM Users.

### Context

Administrative access to the Cloud Platform's AWS account is used by the Cloud Platform team's engineers. This is so they can:

- access the AWS Console, to understand the AWS infrastructure and occasionally to do administrative actions (such as emergency restoring a backup EBS)
- authenticate on the command-line, to run 'terraform plan' while developing or reviewing terraform changes, for example

Existing administrative access has been provided to these people like this:

- signing into the AWS Console using current methods:
- SAML login - using GitHub (as Identity Provider), Auth0 (broker) and AWS SAML Federation
- Console password and MFA (for people who SAML didn't work), for their IAM User
- access key for their IAM User

With existing SAML login, Auth0 acts as an OIDC/SAML broker, with Rules that ensures the user is a member of the `ministryofjustice` GitHub organization, and sets the AWS Role that can be assumed, corresponding to their GitHub teams. A couple of team members have not been able to get this method to work, and have been given username/password/MFA access instead.

- Ownership of the is not with the CP team any more - we need PR approval of the AWS organization root account to change the GitHub group(s) and their permissions. However admin permissions don't change much. And we can describe the [change in terraform](https://github.com/ministryofjustice/aws-root-account/blob/89c75d19663ce7d65588c3ee91cde724caba68c5/terraform/sso-admin-account-assignments.tf#L77-L86) so it really is just a PR approval we'd need.

### Factors in the decision

Pros:

- SSO makes it easy to login to different roles and accounts without having to store different credentials. This allows us to have a read-only role, which the team uses by default, which is safer than using full permissions all the time - a "least privilege" security benefit. And it makes it easier to administer other AWS accounts that use SSO, like DSD. In comparison, the SAML solution doesn't appear to have a way to select different roles, and selecting between AWS accounts means using different login URLs, which is less convenient.
- SAML solution is flakey. A couple of people haven't been able to get the SAML method working, falling back to user a username/password. This is not ideal as the team have to remember to remove them in their leaver process, rather than being able to rely on the standard IT-managed leaver process that removes them from the GitHub organization.
- With SSO we don't have to create and remove IAM Users, like we did with SAML.
- Temporary AWS credentials are more secure than long-lived ones, and whilst this is already the case for console access, SSO provides this for command-line access too

Cons:

- The SSO login is only temporary, so login needs to be easy and get the team used to doing it. TODO What is existing SAML login timeout? TODO Can AWS Vault help with this?

### Security

TODO: Is this 2FA? Can/should we need that? GitHub login requires 2FA. TODO: readonly / timeout TODO: revoking creds of engineers that leave TODO: credentials in plain text on hard disk TODO: update runbooks with use of creds? e.g. export AWS_PROFILE=moj-cp TODO: do we have auditability of AWS actions, since everyone is sharing a role?

### How it will work

The proposed login works like this:

- 1. Users go to https://moj.awsapps.com/start#/ which redirects you to login.
- 2. Auth0 log-in selection page. User selects "Continue with GitHub".
- 3. GitHub login page. If already logged into GitHub, it's skipped.
- 4. AWS page to select account, role and either console or command-line access. For CP users their roles could be: AdministratorAccess or Readonly
- 5. Select either:

**AWS Console** The user is logged in with a federated role, such as: `AWSReservedSSO_AdministratorAccess_bffb036637b86425/davidread@digital.justice.gov.uk`. After the creds time-out, the console prompts you to "relogin", and a single click you're back in.

OR

**CLI** It shows commands to paste into a command-line, to set a temporary access key. After the time-out, they need to redo this from step 1.

Users may prefer the added convenience of using AWS Vault, which works like this:

- 1. User sets up a profile in their `.aws/config`:

[profile cp] sso_start_url=https://moj.awsapps.com/start sso_region=eu-west-2 sso_account_id=754256621582 sso_role_name=AdministratorAccess

- 2. For **AWS Console**:

aws-vault login cp

OR for **CLI**:

aws-vault exec cp -- aws s3 ls

You have to click a link in the browser to login.

- 3. They are prompted for their storage password to save/retrieve a token (this is the case for MacOS keychain, and may differ for other secret storage mechanisms)
- 4. The browser will check you're logged into GitHub and invite you to click through an AWS login page. Both store cookies, so this step rarely needs doing after the first time.

Access for both Console and CLI expires after the time-out. The user re-establishes the connection from the command again (step 2). TODO: check this is correct

## 25 Domain names

Date: 2021-07-07

### Status

✅ Accepted

### Introduction

The "cluster-specific" domain names *.apps.live-1.cloud-platform.service.justice.gov.uk need addressing with the new EKS cluster which is not called `live-1` any more. This is also an opportunity to review all our domain names that are part of Cloud Platform.

### Wildcard domain for apps

**Decision:** deprecate *.apps.live-1.cloud-platform.service.justice.gov.uk

**Decision:** use instead *.apps.cloud-platform.service.justice.gov.uk

#### Context

Tenants have used the `live-1.` domain pattern for their dev and staging environments, following CP [guidance](https://user-guide.cloud-platform.service.justice.gov.uk/documentation/other-topics/custom-domain-cert.html#using-a-custom-domain). It is easy for teams to configure this sort of domain name, because Cloud Platform provides a wildcard SSL/TLS certificate for them. The team implements this by configuring an ingress, which leads to externel-dns setting the DNS name to point at the NLB.

#### Reasoning

Removal of `.live-1` - there is an issue with using a specific cluster name `live-1` with the migration to a new cluster. During the hours of migration, service teams will gradually direct more traffic to the new cluster. This is achieved by having a two DNS entries for the service, created by external-dns, with variable weights. So the cluster name is irrelevant and confusing in this name. So we deprecate it and ask people to remove the `.live-1` from their domain names. During and after This change is a burden for service teams, but it only affects internal users of apps, because production environments [must use a custom domain](https://ministryofjustice.github.io/technical-guidance/documentation/standards/naming-domains.html#cloud-and-modernisation-platform-subdomains), and we will give them several months before removing the name.

`.cloud-platform` - having this in the domain makes it easy to delegate NS for each platform. It can't be abbreviated due to our [Naming Things standard](https://ministryofjustice.github.io/technical-guidance/documentation/standards/naming-things.html

`.service.justice.gov.uk` - is for all pre-beta services and all pre-prod environments, as per [Naming Domains standard](https://ministryofjustice.github.io/technical-guidance/documentation/standards/naming-domains.html)

### Custom app domain e.g. myapp

**Existing decision**: myapp.service.justice.gov.uk for prod environments, pre-beta assessment (no change)

**Existing decision**: myapp.service.gov.uk for prod environments, post-beta assessment (no change)

A custom domain is encouraged for prod environments, rather than the wildcard, because it is shorter and more official looking. If a service passes beta assessment then they move to the GDS-managed `service.gov.uk` domain. This is all to meet the [Naming Domains standard](https://ministryofjustice.github.io/technical-guidance/documentation/standards/naming-domains.html)

Cloud Platform supports for the configuration of custom domains - see guidance: [Using a custom domain](https://user-guide.cloud-platform.service.justice.gov.uk/documentation/other-topics/custom-domain-cert.html#using-a-custom-domain)

### Cloud Platform owned application domains e.g. cloud-platform-reports

#### Non-cluster-specific domains

**Existing decision**: reports.cloud-platform.service.justice.gov.uk

#### Cluster-specific domains

**Decision:**

- live:   *.prod.cloud-platform.service.justice.gov.uk
- live-2: *.non-prod.cloud-platform.service.justice.gov.uk

#### Reasoning

Removal of `.live` - there is an issue with using a specific cluster name such as `live`. The cluster name is irrelevant and confusing in this name. Changes to these domains due to a change in the name of a cluster creates confusion and unnecessarily changes for users. With an alias (instead if cluster name), cloud platform applications can move clusters without requiring a domain name change. We will deprecate and remove the `.live` from domain names.

Current cluster-specific domains requiring a non-cluster-specific domain will be redirected to a landing page with links to all domains and descriptions of each.

### Cluster-specific domains during migration

**Decision**: *.apps.live.cloud-platform.services.justice.gov.uk for use around migrations

In the period  and during migration, service teams will want to test their service running on a particular cluster. For example they may deploy a copy of their service to a new cluster, and wish to test it, before any public traffic is directed to it. So for this purpose we will provide cluster-specific domains.

A future migration might introduce:

- *.apps.live-blue.cloud-platform.services.justice.gov.uk
- *.apps.live-green.cloud-platform.services.justice.gov.uk

Once the migration is complete we should remove these domains and wildcard cert, because we want service teams to use the non-cluster specific domain (or cluster domain) in general use, so that this traffic can be transferred smoothly to a new cluster in the next migration, and old clusters can be switched off.

### Manager domain

**Existing decision**: *.apps.manager.cloud-platform.services.justice.gov.uk

The manager cluster has a separate pattern of URLs and wildcard cert, keeping it separate from the main clusters.

## 26 Managed Prometheus

Date: 2024-11-11

### Status

🤔 Proposed

### Proposal

Use [Amazon Managed Service for Prometheus](https://aws.amazon.com/prometheus/) (AMP) for monitoring Cloud Platform, instead of a self-managed instance of Prometheus.

### Context

#### Monitoring metrics

It's good operational practice to have good 'observability'. This includes monitoring, achieved by regular checking the metrics, or health numbers, of the containers running. The timeseries data which is collected can be shown as graphs or other indicators in a dashboard, and evaluated against rules which trigger alerts to the operators. Typical use by operators include:

- to become familiar with the typical quantity of resources consumed by their software
- to be alerted to deteriorating health, so that they can fix it, before it becomes an incident
- being alerted to an incident, to be able to react quickly, not just when users flag it
- during an incident getting an at-a-glance overview of where problems exist
- after an incident to understand what went wrong, and help review the actions taken during the response
- reviewing long-term patterns of health

#### Choice of Prometheus

Prometheus has been used by Cloud Platform for monitoring metrics since being established in 2017. CP have used Prometheus for a number of years and are happy with its functionality. Prometheus remains a popular choice in industry, is open source with a large community, and is [recommended by CNCF](https://raw.githubusercontent.com/cncf/trailmap/master/CNCF_TrailMap_latest.png).

**Commercial proprietary options**: The CP team has [investigated](https://docs.google.com/document/d/1eG2Fd4G8f_bPBYnNAwE2seF2PdNXsxjggsqck6IXNeI/edit) some commercial monitoring solutions, such as DataDog, Splunk, Honeycomb. These tend to do several related things, including metric monitoring, dashboard, alerting, logging and application performance monitoring. They don't offer any functionality we particular need. But it's nice that monitoring and logging are nicely integrated. Having it as a managed service, would reduce operations, and having to architect for future scaling. There was some concern about off-shoring log data, for circumstances where personal data leaks into logs. The cost varied $10k - $160k. There is some suggestion that even with a managed service, we'd still need to retain some use of Prometheus. There were concerns about users' config as code - whether it was as easy to deploy as it is with open source. And there would be the cost of migration users config would need migrating from their existing Prometheus/AlertManager/Grafana syntax.

So overall we are happy to stick with Prometheus.

#### How CP uses Prometheus

Prometheus is setup to monitor the whole of Cloud Platform, including:

- Tenant containers
- Tenant AWS resources
- Kubernetes cluster. kube-prometheus

Prometheus is configured to store 24h worth of data, which is enough to support most use cases. The data is also sent on to Thanos, which efficiently stores 1 year of metrics data, and makes it available for queries using the same PromQL syntax.

Alertmanager uses the Prometheus data when evaluating its alert rules.

#### Concerns about hosting Prometheus (as we currently do)

The Prometheus container has not run smoothly in recent months:

- **Performance (resolved)** - There were some serious performance issues - alert rules were taking too long to evaluate against the Prometheus data, however this was successfully alleviated by increasing the disk iops, so is not a remaining concern.
- **Custom node group** - Being a single Prometheus instance for monitoring the entire platform, it consumes a lot of resources. We've put it on a dedicated node, so it has the full resources. And it needs more memory than other nodes, which means it needs a custom node group, which is a bit of extra management overhead.
- **Scalability** - Scaling in this vertical way is not ideal - scaling up is not smooth and eventually we'll hit a limit of CPU/memory/iops. There are options to shard - see below.

We also need to address:

- **Management overhead** - Managed cloud services are generally preferred to self-managed because the cost tends to be amortized over a large customer base and be far cheaper than in-house staff. And people with ops skills are at a premium. The management overhead is:
- for each of Prometheus, kube-prometheus
- **High availability** - We have a single instance of Prometheus, simply because we've not got round to choosing and implementing a HA arrangement yet. This risks periods of outage where we don't collect metrics data. Although the impact on the use cases is not likely to be very disruptive, there is some value in fixing this up.

#### Options for addressing the concerns

**Thanos take load off Prometheus**: It's been suggested we could reduce load on Prometheus by it only retaining say 2h of logs, and shift as much as possible of the work to Thanos. However since the latest data is what you want to be running most queries and alert rules on, it is not clear how close to real-time Thanos can be kept. And Thanos rules are [unreliable](https://github.com/thanos-io/thanos/blob/main/docs/components/rule.md#risk)). This would likely reduce the load on Prometheus, but it may only be temporary, and it might simply shift the scalability concerns onto Thanos.

**Sharding**: We could split/shard the Prometheus instance: perhaps dividing into two - tenants and platform. Or if we did multi-cluster we could have one Prometheus instance per cluster. This appears relatively straightforward to do. There would be concern that however we split it, as we scale in the future we'll hit future scaling thresholds, where it will be necessary to change how to divide it into shards, so a bit of planning would be needed.

**High Availability**: We are now running Prometheus in HA mode [with 3 replicas](https://github.com/ministryofjustice/cloud-platform-terraform-monitoring/pull/239). Keeping the findings below as we may have some additional elements of HA to consider in the future:

> [Source](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/high-availability.md#prometheus) There is a `replicas` option to do this. However for HA we would also need to have a load balancer for the PromQL queries to the Prometheus API, to fail-over if the primary is unresponsive. And it's not clear how this works with duplicate alerts being sent to AlertManager. This doesn't feel like a very paved path, with Prometheus Operator [saying](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/high-availability.md) "We are currently implementing some of the groundwork to make this possible, and figuring out the best approach to do so, but it is definitely on the roadmap!" - Jan 2017, and not updated since.

**Managed Prometheus**: Using a managed service of prometheus, such as AMP, would address most of these concerns, and is evaluated in detail in the next section.

#### Evaluation of managed Prometheus

Managed Prometheus, such as AMP, would out-source the operational concerns, including performance and scalability, as well as management of custom node groups. We'll examine these against the at a financial cost. And potentially monitoring from outside the VPC will change the architecture. This ADR aims to understand all these issues. Specifically interested in Amazon Managed Service for Prometheus (AMP).

Scaling: AMP scales automatically, without configuration.

High Availability: AMP is highly available and distributed across multiple AZs automatically. In contrast there are question marks about how to do this with self-hosted - see above.

Resilience: AMP is relatively isolated against cluster issues. The data kept in durable storage, away from the cluster.

Lock-in: the configuration syntax and other interfaces are the same or similar to our existing self-hosted Prometheus, so we maintain low lock-in / migration cost.

#### Existing install

The 'monitoring' namespace is configured in [components terraform](https://github.com/ministryofjustice/cloud-platform-infrastructure/blob/main/terraform/aws-accounts/cloud-platform-aws/vpc/eks/core/components/monitoring.tf) calling the [cloud-platform-terraform-monitoring module](https://github.com/ministryofjustice/cloud-platform-terraform-monitoring). This [installs](https://github.com/ministryofjustice/cloud-platform-terraform-monitoring/blob/main/prometheus.tf#L88) the [kube-prometheus-stack Helm chart](https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/README.md) / [kube-prometheus](https://github.com/prometheus-operator/kube-prometheus) (among other things).

[kube-prometheus](https://github.com/prometheus-operator/kube-prometheus) contains a number of things:

- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator) - adds kubernetes-native wrappers for managing Prometheus
- CRDs for install: Prometheus, Alertmanager, Grafana, ThanosRuler
- CRDs for configuring: ServiceMonitor, PodMonitor, Probe, PrometheusRule, AlertmanagerConfig
- allows specifying monitoring targets using kubernetes labels
- Kubernetes manifests
- Grafana dashboards
- Prometheus rules
- example configs for: node_exporter, scrape targets, alerting rules for cluster issues

High Availability - not implemented (yet).

Resilience - In the absence of HA, some resilience is offered by the presence of a back-up node. If the node on which Prometheus instance is running fails, then the back-up node is ready to run a Prometheus instance, so downtime is capped at 2 minutes. The back-up node is the same spec and configuration. It is running in the same AZ, so that it can access the same EBS with the Prometheus data. https://github.com/ministryofjustice/cloud-platform/issues/1749#issue-587058014

Prometheus config is held in k8s resources:

- ServiceMonitor
- PrometheusRule - alerting

### How it would work with AMP

We've spiked a terraform module to implement this: https://github.com/ministryofjustice/cloud-platform-terraform-amp

A 'forwarding' Prometheus instance installed in the cluster, which scrapes data, keeps a copy and uses "remote write" to forward all of its data to AMP. This transfer looks pretty robust, using a write ahead log and queue.

The forwarding Prometheus could simply be the standard community Helm chart: https://prometheus-community.github.io/helm-charts which is simple and makes upgrades easy. We don't need kube-prometheus any more. It doesn't need to store much - just enough to forward it to AMP. TODO work out if the link to AMP breaks down for a period.

(This arrangement is the same as [what AP do](https://github.com/moj-analytical-services/analytical-platform-flux/blob/main/clusters/development/prometheus/prometheus.yaml)). The Prometheus Helm chart configures Prometheus to scrape k8s resources that have [prometheus.io annotations](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus#scraping-pod-metrics-via-annotations). However we'll let users define ServiceMonitor configs as before.)

Storage: - you can throw as much data at it. Instead there is a days limit of 150 days. This is plenty long enough for the use cases, so no need for **Thanos**, so this is very useful.

Alertmanager:

- AMP has an Alertmanager-compatible option, which we'd use with the same rules
- Sending alerts would need to us to configure: create SNS topic that forwards to user Slack channels

Grafana:

- Amazon Managed Grafana has no terraform support yet so just setup in AWS console. So in the meantime we stick with self-managed Grafana, which works fine.

Prometheus web interface - previously AMP was headless, but now it comes with the web interface

Prometheus Rules and Alerts:

- In our existing cluster:
- we get ~3500 Prometheus rules from: https://github.com/kubernetes-monitoring/kubernetes-mixin
- kube-prometheus compiles it to JSON and applies it to the cluster
- So for our new cluster:
- we need to do the same thing for our new cluster. But let's avoid using kube-prometheus. Just copy what it does.
- when we upgrade the prometheus version, we'll manually [run the jsonnet config generation](https://github.com/kubernetes-monitoring/kubernetes-mixin#generate-config-files), and paste the resulting rules into our terraform module e.g.: https://github.com/ministryofjustice/cloud-platform-terraform-amp/blob/main/example/rules.tf

#### Still to figure out

##### Tenants' rules and alerts

Tenants [create PrometheusRule k8s resources by kubectl apply](https://user-guide.cloud-platform.service.justice.gov.uk/documentation/monitoring-an-app/how-to-create-alarms.html#create-a-prometheusrule) or in environments repo. How are we going to get this config inserted into AMP? Could it just be a cronjob that copies these resources' config into AMP? (We do something similar for Grafana.) And we should check that invalid rules don't get applied and cause problems for other tenants.

##### Costs

Look at scale and costs. Ingestion: $1 for 10m samples

Prices (Ireland):

- EU-AMP:MetricSampleCount - $0.35 per 10M metric samples for the next 250B metric samples
- EU-AMP:MetricStorageByteHrs - $0.03 per GB-Mo for storage above 10GB

##### Region

AMP is not released in the London region yet (at the time of writing, 3/11/21). However we could run it in another region - data ingestion into the regio is free - we would pay only for the Grafana queries.

##### Other components we use

We should check our usage of these related components, and if we still need them in the new cluster:

- CloudWatch exporter
- Node exporter
- ECR exporter
- Pushgateway

##### Showing alerts

We need to show users their alerts - both the config and their firing. Currently they use alertmanager's web interface - so we'll need an equivalent.

Maybe we could run alertmanager itself, purely for this purpose, but rely on AMP's alertmanager for actually sending them? But they would show up as inactive, and might expose differences in functionality.

Or maybe we can give users read-only access to the console, for their team's SNS.

##### Workspace as a service?

We could offer users a Prometheus workspace to themselves - a full monitoring stack that they fully control. Just a terraform module they can run. Maybe this is better for everyone, than a centralized one, or just for some specialized users - do some comparison?

## 27 AWS Console access for users

Date: 2021-11-03

### Status

🤔 Proposed

### Proposal

Give users (developers in service teams) access to the AWS Console of the Cloud Platform AWS account, so they could view their team's resources.

Implementation:

- AWS resources are tagged by the k8s namespace name, to which they are attached (simply added into our Terraform modules)
- Users would sign into the console using AWS SSO
- CP would set-up authorization in [ABAC](https://docs.aws.amazon.com/singlesignon/latest/userguide/abac-checklist.html), to give users access to their team's resources. Specifically it connects the user's GitHub team(s) with resource tags, using the mappings in the environment repo.

This would give teams console access to their backing resources, including RDS database, ECR, S3, etc.

TODO decide if they are somehow allowed write access - see discussion below.

Note: they would not have access to platform infrastructure, including the cluster which runs their containers, or the NLB where their user traffic ingresses. These are shared resources.

### Context

A key value of CP is to support teams to use **infrastructure as code**, rather than **ClickOps**. IaC benefits:

- Infrastructure that you tested in the dev environment is going to be exactly the same in production. Whereas ClickOps risks deploying something different
- You can recreate infrastructure from scratch, confident their config is correct. Otherwise you gradually find yourself with 'configuration drift', meaning it is 'snowflake infrastructure', which you cannot risk recreating or recover from failure

With this in mind, CP has been designed so that users define their AWS resources in terraform. This pushes them to use the best practice of 'infrastructure as code', and they are supported in that practice, because CP team writes and maintains most of the terraform modules that they call, and maintain the CI/CD to apply it.

### User needs

"AWS Console Access" can be provided in chunks, outlined below. Each are described with the user needs that have been gathered from chats with users and TA thoughts, pending the proper user research.

#### **Read-only** access to **user's AWS resources**

Users could see their RDS database etc. (This doesn't include the machine/networking where their app runs, nor the ingress)

- **Learning and understanding** - The console is much more user-friendly than terraform (or the CLI/API). This is good for understanding what is configured, learning about configuration options, and generally learning AWS/cloud. The console communicates a lot about how the options fit together, current state and show  guidance and warnings, so are great for building a mental model of a service. Tutorials from AWS, CloudGuru, etc use the console, for even the most advanced services, so using the console to learn is a strong convention.
- **Visual feedback** - During usage, some services have state that is particularly useful to view in the console - RDS Performance Insights and Step Functions provide information in a very visually intensive way, and it is unreasonable to try and get the same experience via CLI or API.

#### **Read-only** access to **platform infrastructure**

Users could see config of the machine/networking where their app runs, and ingress (load balancer, WAF, DNS)

- **CP understanding** - Users benefit from seeing behind the CP interfaces, to see how the platform works. Reasoning:
- for interests sake and their learning of cloud
- knowing how something works enables you to use it better
- so that they can evaluate it better from a security point of view, seeing the config of VPC, security groups, etc, and the console is how they are used to viewing this things

#### **Write** access

Users could change the to:

- **user's AWS resources** - their RDS database etc.
- **ingress** - DNS, WAF

Use cases:

- **Quick iteration** when you're still trying stuff out or getting something to work, e.g. changing a port number, DNS setup
- **One-off operations**, such as upgrading a database version, triggering a database snapshot or restore, DNS cut-overs

If giving users write access to the console, the concern would be not to allow long-lasting configuration changes.

Perhaps a solution would be:

- quick iterations would be allowed, as long as there is an understanding that at the end of the day or week it will be automatically reverted to what the terraform has configured
- one-off actions could maybe be identified and allowed

### Design - Read-only access to user's AWS resources

One way to do it:

- Users login via SSO, with a role for their team
- AWS resources should already be tagged by the owning team.
- IAM created to allow each team role to access resources tagged against that team - https://docs.aws.amazon.com/IAM/latest/UserGuide/access_tags.html
- Concourse pipeline for creating the roles and permissions

There may be a more sophisticated way - maybe AWS folks can suggest.

### Progress

21/1/22 Team is confident that read-only access is a user priority, so focussing on this. User research is in progress to evidence and flesh out the user needs. Work is underway to design how it could work.

## 28 Repo vulnerability scanning

Date: 2021-11-05

**Link to this ADR: https://docs.google.com/document/d/1s8UDD8eiAN8cD9gRgHi6KhNe6C4V0wuo5EFwvyvGy2w/edit#**

(Security-related ADRs are stored privately. It's useful to keep this sign-post here, so it is findable with all the other ADRs)

## 29 Kubernetes security config auditing

Date: 2021-11-10

**Link to this ADR: https://docs.google.com/document/d/1PW2LF7rhf5w96L8j-w5z4gd_odfmA9MWXyGuD5TWqGk/edit#**

(Security-related ADRs are stored privately. It's useful to keep this sign-post here, so it is findable with all the other ADRs)

## 29 Kubernetes security config auditing

Date: 2021-12-09

**Link to this ADR: https://docs.google.com/document/d/12__IvU126-GZtltMEm7BH7bNlKh8xLfjnLnNYloNilA/edit#heading=h.49vl3zxwy062**

(Security-related ADRs are stored privately. It's useful to keep this sign-post here, so it is findable with all the other ADRs)

## 31 Image vulnerability scanning

Date: 2022-01-05

**Link to this ADR: https://docs.google.com/document/d/1CsW_RF0pB2cFSc2y__YfQwjQdWBtccq3Ug1EyjVkW88/edit#**

(Security-related ADRs are stored privately. It's useful to keep this sign-post here, so it is findable with all the other ADRs)

## 33 Manager cluster

Date: 2022-01-07

### Status

✅ Accepted (documenting an existing thing)

### The existing decision

We have a 'Manager cluster', for running infrastructure CI/CD (Concourse), which is separate to the clusters that run user workloads.

### Context

On the Manager cluster we run:

- Concourse
- Thanos compactor
- Hoodaw report generators

Reasons to run these workloads separate to the main cluster:

- 1. **Recovering the main cluster** - Concourse deploys infrastructure, including EKS. So if it runs on the same cluster that it creates, we may encounter a "chicken and egg problem". For example if the live cluster is damaged, then we would want to reapply that infrastructure with Concourse, so it makes sense to run it on another cluster. (This arrangement however doesn't cover some other scenarious - it runs in the same AWS account and VPC, so might not recover some issues with those things, or bootstrap a fresh install.)
- 2. **Test cluster** - It seems genuinely useful to test applying changes to the Manager cluster before they are applied to Live, particularly significant ones like kubernetes upgrades. We already test on a (personal) Test cluster, but the Manager cluster runs more life-like workloads, and there is more pressure to apply changes to it without downtime.
- 3. **Security isolation of CI/CD** - it's a good security practice to run CI/CD separately to where the app runs. CI/CD tends to need wide permissions to build containers, and to deploy things. Admin access to CI/CD needs to be only for admins, whereas apps are often public. There is a clear difference in needs for Concourse and the apps, so to minimize risks and attack surface, it makes sense to separate off Concourse from the live cluster(s).

## 34 EKS Fargate

Date: 2022-01-21

### Status

🤔 Incomplete

### Proposal

Move from EKS managed nodes to EKS Fargate.

### Discussion

This is really attractive because:

- to reduce our operational overhead
- improve security isolation between pods (it uses Firecracker, so we can stop worrying about an attacker managing to escape a container).

However there’s plenty of things we’d need to tackle, to achieve this (copied from [ADR022 EKS - Fargate considerations](https://github.com/ministryofjustice/cloud-platform/blob/main/architecture-decision-record/022-EKS.md#future-fargate-considerations)):

**Pod limits** - there is a quota limit of [500 Fargate pods per region per AWS Account](https://aws.amazon.com/about-aws/whats-new/2020/09/aws-fargate-increases-default-resource-count-service-quotas/) which could be an issue, considering we currently run ~2000 pods. We can request AWS raise the limit - not currently sure what scope there is. With Multi-cluster stage 5, the separation of loads into different AWS accounts will settle this issue.

**Daemonset functionality** - needs replacement:

- fluent-bit - currently used for log shipping to ElasticSearch. AWS provides a managed version of [Fluent Bit on Fargate](https://aws.amazon.com/blogs/containers/fluent-bit-for-amazon-eks-on-aws-fargate-is-here/) which can be configured to ship logs to ElasticSearch.
- prometheus-node-exporter - currently used to export node metrics to prometheus. In Fargate the node itself is managed by AWS and therefore hidden. However we can [collect some useful metrics about pods running in Fargate from scraping cAdvisor](https://aws.amazon.com/blogs/containers/monitoring-amazon-eks-on-aws-fargate-using-prometheus-and-grafana/), including on CPU, memory, disk and network

**No EBS support** - Prometheus will run still in a managed node group. Likely other workloads too to consider.

**How people check the status of their deployments** - to be investigated

**Ingress can't be nginx? - just the load balancer in front** - to be investigated. Would be fine with AWS Managed Ingress

If we don't use Fargate then we should take advantage of Spot instances for reduced costs. However Fargate is the priority, because the main driver here is engineer time, not EC2 cost.

## Deprecated TLS Versions

Date: 04/07/2022

### Status

✅ Accepted

### Context

The current Cloud Platform Ingress Controllers support TLS 1.0, 1.1, and 1.2. This is due to end users of services being hosted on the platform having to rely on unsupported browser versions. We have had to retain for older TLS versions to support this ongoing dependancy.

Since the original decision to support older TLS versions a number of things have happended:

- 1. TLS version 1.3 needs to be supported
- 2. The user estate has undergone a number of end user device refreshes which have introduced modern browsers
- 3. There is a recurring issue of legacy TLS versions being identified in Service Team ITHCs
- 4. [NCSC Guidance on legacy TLS versions](https://www.ncsc.gov.uk/guidance/using-tls-to-protect-data#section_5)

We are now offering users new Ingress Controllers that offer support for 1.2 and 1.3, and we need to plan how we will manage the older versions of TLS.

### Decision

Remove support for TLS versions 1.0 and 1.1 on the new Ingress Controller.

Add support for TLS version 1.3

### Consequences

There is a small risk that a user on the estate may be using an unsupported browser that uses a deprecated version of TLS. Following a number end user device refresh projects we believe that users have been moved to browsers that support modern TLS versions.

To mitigate this risk we will advise our users to move non-production workloads first, test that moving to the new ingress controller doesn't cause an issuses, and then move production workloads.

Removing unsupported TLS versions will improve security on the platform.

## 36. Multi-cluster

Date: 2022-09-16

### Status

✅ Accepted

### Context

At the time of writing (16th September, 2022); Cloud Platform hosts user applications in a single Kubernetes cluster. On 12th April, 2022, we decommissioned the [old kOps cluster](https://github.com/ministryofjustice/cloud-platform-environments/commit/2a36ba40562ff77e64dd18d1e1fca3f253e38c80) in favour of utilising EKS (see [ADR-022 - EKS](022-EKS.md)).

At the time of decommissioning the kOps cluster, Cloud Platform [hosted 409 namespaces](https://github.com/ministryofjustice/cloud-platform-environments/tree/2a36ba40562ff77e64dd18d1e1fca3f253e38c80/namespaces/live.cloud-platform.service.justice.gov.uk) in the new EKS-based Kubernetes cluster.

The key reasoning behind utilising a single Kubernetes cluster for service teams is described in [ADR-021](021-Multi-cluster.md), namely:

- Strong isolation is already required between apps from different teams (via namespaces, network policies), so there is no difference for isolating environments
- Maintaining clusters for each environment is a cost in effort
- You risk the clusters diverging. So you might miss problems when testing on the dev/staging clusters, because they aren't the same as prod.

However, outside of service teams applications; the Cloud Platform does already use multiple clusters for 'management', and ephemeral 'test' purposes, and further information regarding multi-cluster and its challenges are described in [ADR-021](021-Multi-cluster.md).

The Cloud Platform team's use of EKS has matured and usage of the EKS-based cluster has grown since April from 409 namespaces, to 457 at the time of writing and will continue to grow in the future. Due to this, we believe now is a good time to start separating out workloads into a multi-cluster environment, as the nuances and costs of EKS are more widely understood.

It is worth noting that the current cluster (at the time of writing) is not considered a ["large cluster" by Kubernetes](https://kubernetes.io/docs/setup/best-practices/cluster-large/), which stipulates these considerations for a "large cluster":

- No more than 110 pods per node
- No more than 5000 nodes
- No more than 150000 total pods
- No more than 300000 total containers

The Cloud Platform is not near these limits.

### Decision

We have decided to:

- adopt a multi-cluster approach
- start adopting multi-cluster by splitting out workloads by _environment type_, i.e. _production_ and _non-production_
- treat the _non-production_ cluster as a second _production_ cluster within the team, though there may be slight differences such as:
- compute power, where _non-production_ workloads don't require as intensive power as _production_ workloads
- hours of operation, for e.g. we may turn off the non-production cluster out of hours or on weekends if there is appetite to do so with our users to save on cost
- we will allow users to self-select their preferred environment initially, though this may change or automate in the future

### Consequences

By running multiple clusters, we can:

- derisk upgrading Kubernetes versions as non-production workloads will be separate from production workloads
- reduce the blast radius by creating a hard separation between clusters
- reduce the cluster single-points of failure, such as ingress controllers
- increase our separation outside of Kubernetes between workloads
- improve our resilience
- we can customise the non-production cluster to meet non-production needs, and the production cluster to meet production needs

However, this does come at both a monetary and team cost:

- we expect the cost of running the Cloud Platform to increase, not significantly but not insignificantly
- there will be less efficient resource usage as some nodes may not fill up
- there will be an increased complexity of cluster management

## 37. Serverless (Lambda/Functions-as-a-Service)

Date: 2022-09-22

### Status

❌ Rejected

### Context

#### Overview

The Cloud Platform team often gets questions regarding the use of "serverless" within the context of the Cloud Platform. The Cloud Platform is (at the time of writing) hosted on AWS, and their definition of "serverless" products is:

- AWS Lambda _(Functions-as-a-Service)_
- Amazon API Gateway _(APIs-as-a-Service)_
- Amazon DynamoDB _(Serverless key value store)_
- Amazon EventBridge _(Serverless event bus)_
- Amazon Simple Notification Service (SNS) _(Serverless messaging service)_
- Amazon Simple Queue Service (SQS) _(Serverless queuing service)_
- Amazon Simple Storage Service (S3) _(Serverless file store)_
- AWS AppSync _(Serverless GraphQL / pub/sub)_
- AWS Fargate _(Serverless compute for containers)_
- AWS Step Functions _(Serverless state machine)_

The Cloud Platform does support the usage of some of these services already (namely [DynamoDB](https://github.com/ministryofjustice/cloud-platform-terraform-dynamodb-cluster), [SNS](https://github.com/ministryofjustice/cloud-platform-terraform-sns-topic), [SQS](https://github.com/ministryofjustice/cloud-platform-terraform-sqs), [S3](https://github.com/ministryofjustice/cloud-platform-terraform-s3-bucket)).

The most common query in the context of serverless is the ability for teams to use AWS Lambda, which is the focus of this ADR.

##### What is the Cloud Platform?

The Cloud Platform is a centralised platform, utilising Kubernetes, which is running containerised workloads. This is provided as a _platform-as-a-service_ to the wider Ministry of Justice. See [What is the Cloud Platform?](https://user-guide.cloud-platform.service.justice.gov.uk/documentation/concepts/what-is-the-cloud-platform.html#what-is-the-cloud-platform) for more information.

##### What is AWS Lambda?

[AWS Lambda](https://aws.amazon.com/lambda/) provides the (self-described) ability to "run code without provisioning or managing infrastructure". Lambda supports container images (if they implement the [runtime interface client](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-images.html#runtimes-api-client)) or directly as code.

#### Cloud Platform **is** serverless

The widely accepted answer for "what is serverless" is that teams _don't need to manage underlying servers for the services they run_. In this context, the Cloud Platform _is_ in itself serverless. The Cloud Platform team is the provider in this case, who manage the "underlying servers" (in the context of cloud), networking infrastructure, etc. This is in the same way that typical AWS Lambda usage is also serverless.

#### Our thoughts on using AWS Lambda/Functions-as-a-Service in the Cloud Platform

When people raise serverless usage with the Cloud Platform team, they usually have different reasons for doing so, so it is impossible to list and answer each question separately, so this is limited to the _common_ thoughts on using AWS Lambda/Functions-as-a-Service in the context of Cloud Platform:

- 1. Cloud Platform is already serverless

The Cloud Platform itself is already serverless for users, they don't need to manage the underlying infrastructure or common network configuration between their service and elsewhere.

- 2. We can't (currently) provide a good developer experience when using AWS Lambda

Cloud Platform provides read-only access to _users_ of the Cloud Platform, to encourage infrastructure-as-code and standardise infrastructure deployment across the MOJ. AWS Lambda functions need to be uploaded often (when changed, for e.g.), and our current pipeline for _infrastructure_ deployment utilises the [cloud-platform-environments](https://github.com/ministryofjustice/cloud-platform-environments) repository, which requires one of the Cloud Platform team to approve for deployment. This can become frustrating for debugging Lambda or initially configuring it.

- 3. There is little monetary benefit for using serverless in the context of what Cloud Platform currently hosts

Small services running on the Cloud Platform, even if idle, are very cheap to run anyway in the wider context of the Cloud Platform. This cost is also (as with all services running on Cloud Platform) absorbed by the Cloud Platform team.

- 4. We don't currently have safeguards or common, reusable functionality in place for using Functions-as-a-Service

The Cloud Platform currently has out-of-the-box functionality for basic alerting, monitoring, and logging that has been standardised for use across every service that runs on Cloud Platform. However, we would need to start from scratch to implement feature parity for the use of AWS Lambda (and Functions-as-a-Service generally), which can create a derivation in standardisation. This derivation is linked to the risk appetite across several teams, including the service team, Cloud Platform team, and other stakeholders.

- 5. There is appetite across MOJ teams to explore the use of Functions-as-a-Service

It's worth noting that there _is_ growing appetite for teams to start exploring the use of Functions-as-a-Service, and we typically revisit FaaS offerings that can be run on Kubernetes, such as [Kubeless (now archived)](https://github.com/vmware-archive/kubeless), [OpenFaaS](https://docs.openfaas.com/) and [Knative](https://knative.dev/docs/).

- 6. We treat all infrastructure _and_ services as standard, not unique

Cloud Platform currently treats _all_ provisioned infrastructure for the underlying platforms as standard and replaceable. A typical requirement for a service to run on Cloud Platform is, for example, it to be stateless as per [12FA](https://12factor.net/): so even the _service_ is treated as standard and replaceable. By introducing AWS Lambda (specifically), we start to treat specific services as unique until we hit a tipping point for standardisation of cloud infrastructure and creates divergence both locally (in specific areas of the MOJ) and more generally (across the whole of the MOJ).

### Decision

Based on the above points, we have ❌ rejected the introduction of AWS Lambda/Functions-as-a-Service into the Cloud Platform. On a point-by-point basis:

- 1. Cloud Platform is already serverless for our users (i.e. they don't need to manage infrastructure behind the scenes)
- 2. We can't (currently) provide a good developer experience when using AWS Lambda, which would likely lead to frustration of teams trying to deliver services
- 3. There is little or no monetary benefit to using Functions-as-a-Service in the context of Cloud Platform
- 4. We don't have safeguards or common, reusable functionality in place for using Functions-as-a-Service, and we don't have the capability or time to currently start exploring this
- 5. As there is appetite in the wider MOJ to explore the use of Functions-as-a-Service, Cloud Platform will periodically review Kubernetes integrations with both AWS Lambda (e.g via [AWS Controllers for Kubernetes](https://aws-controllers-k8s.github.io/community/docs/community/overview/)) and more generic Functions-as-a-Service offerings, such as [OpenFaaS](https://docs.openfaas.com/) and [Knative](https://knative.dev/docs/).
- 6. By introducing Functions-as-a-Service (or AWS Lambda) to Cloud Platform, we need to be cognisant and understand how we can treat the underlying infrastructure for it as standard and replaceable; not unique and hand-built.

Further, in March 2022, we conducted user research around the use of serverless and more explicitly, what needs teams across the MOJ are trying to solve with serverless. This research revealed two important points:

- _some_ aspects of serverless are already provided by the team; and adopting a serverless approach won't (by itself) resolve outstanding needs for users, which are already being considered with non-serverless infrastructure
- further research needs to be taken but in-line with more general approaches rather than focussing on serverless as a solution

### Consequences

By rejecting introducing AWS Lambda/Functions-as-a-Service to the Cloud Platform, we (the Cloud Platform team):

- are asking teams to continue using more "traditional" methods for building their services, such as containerised, stateless, and meeting the [12 Factor app methodology](https://12factor.net/)
- will periodicially review Functions-as-a-Service on Kubernetes to see what's happening in the market
- will carry out further research to meet needs using the best technology to meet user needs, rather than focussing on serverless as a solution

## 38. Split Components Infrastructure

Date: 2024-03-04

### Status

🤔 Incomplete

### Context

Following the upgrade to Kubernetes 1.25, PodSecurityPolicy was removed, and the team chose to use Gatekeeper's mutating capabilities to replace the functionality that was previously provided by our PSP configurations. This meant a large change in the way our cluster operates and the modules at a components level. While upgrading it became clear that there are a large number of components dependent on each other that are not required. This makes the component level difficult to work with. We also found modules that used non standard methods of declaring dependency because of the version of terraform used at the time. Removing dependencies at the components level will allow us to focus on future features such as [multi cluster](036-multi-cluster.md) and blue green clusters.

We propose to add a new level to our build process called core. This splits our process into 3 distinct areas within our terraform:

- EKS - Everything required to bring up a basic cluster.
- Core - Core components that are required for our users to be able to safely and securely deploy their application to.
- Components - Optional components that provide additional functionality to a cluster

> Components are not optional in `live` (apart from the starter pack). When testing new components and features all components should be used to make sure there are no edge case issues.

#### Considerations

- Developing this using test clusters will be easier than `live`, documentation and a focus on how we deploy this to `live`, and safely migrate existing terraform state into its new s3 location should be at the front of the work.
- Evaluate each component to determine whether they are core or optional components.
- Prometheus CRDs are a hard requirement on a lot of components, we can split these into `core` but would that increase complexity?
- Each stage must be a concrete deliverable.

### Decision

We have decided to:

- Start planning out the work required to split the components into `core`.
- Document the process of moving components.
- Test changes using test clusters.
- Apply the changes to `live`, `live-2` and `manager`

### Consequences

By implementing this solution we will be decreasing our component level complexity.

It opens up a lot of future roadmap work.

## 39. AWS Network Firewall

Date: 2025-09-16

### Status

✅ Accepted

### Context

We need the ability to control and inspect traffic leaving and entering Cloud Platform EKS VPCs. This is important for:

- Enforcing security policies (e.g. blocking malicious destinations).
- Monitoring outbound connections for compliance and audit.
- Detecting suspicious behaviour, such as unexpected protocols or destinations.
- Protecting workloads by inspecting inbound traffic and blocking known malicious sources.

An earlier idea was to [create a centralised egress VPC] to achieve these goals. However, this ran into problems: test clusters use overlapping CIDRs, which prevents reliable connectivity to a shared egress VPC.

We need an approach that gives us inspection and control now, without large network redesigns.

### Decision

We will deploy [AWS Network Firewall] inside the Cloud Platform VPC.

- The Cloud Platform VPC will route all outbound traffic through firewall subnets before reaching the NAT Gateway and the internet.
- The Cloud Platform VPC will also route inbound traffic through the firewall for inspection before reaching workloads.
- Firewall rule groups (such as domain allowlists, port restrictions, or intrusion detection rules) will be managed centrally in code and applied consistently across the environment.
- Logs will be sent to CloudWatch for monitoring, alerting, and auditing.

We will also create firewall policies with the following threat detection rule groups enabled:

- [AttackInfrastructureStrictOrder] – detects and blocks communication with known attacker infrastructure.
- [MalwareDomainsStrictOrder] – blocks domains associated with malware distribution or activity.
- [BotNetCommandAndControlDomainsStrictOrder] – prevents communication with botnet command-and-control servers.

This ensures that the Cloud Platform VPC has consistent ingress and egress traffic inspection, control, and active threat detection at its edge.

### Consequences

**Pros**

- Provides the required control and inspection of both ingress and egress traffic in the Cloud Platform VPC.
- Adds built-in AWS threat detection for attacker infrastructure, malware, and botnets.

**Cons**

- Ingress and egress inspection may add latency for workloads, requiring performance testing.
- Some threat detection rules may cause false positives, requiring a process for tuning.

[AWS Network Firewall]: https://aws.amazon.com/network-firewall/ [create a centralised egress VPC]: https://github.com/ministryofjustice/cloud-platform/issues/7428 [AttackInfrastructureStrictOrder]: https://docs.aws.amazon.com/network-firewall/latest/developerguide/aws-managed-rule-groups-atd.html [MalwareDomainsStrictOrder]: https://docs.aws.amazon.com/network-firewall/latest/developerguide/aws-managed-rule-groups-domain-list.html [BotNetCommandAndControlDomainsStrictOrder]: https://docs.aws.amazon.com/network-firewall/latest/developerguide/aws-managed-rule-groups-domain-list.html

## 40. Use GitHub Actions

Date: 2026-01-02

### Status

✅ Accepted

### Context

Cloud Platform uses a self managed Concourse instance hosted in a management EKS cluster. This runs all of the Cloud Platform deployment pipelines.

The Cloud Platform will be moving to the Modernisation Platform (see ADR 39), the Modernisation Platform uses GitHub Actions for deployment pipelines.

### Decision

We will switch to using GitHub Actions for our deployment pipelines.

### Consequences

- We will decomission our Concourse pipelines once the move to Modernisation Platform has been completed
- We will decomission our management cluster once the move to Modernisation Platform has been completed
- We will use the Modernisation Platform pipelines where possible
- We will create new GitHub Actions in a our repositories where appropriate

## 41. Decommission the Cloud Platform CLI Tool

Date: 2026-01-02

### Status

✅ Accepted

### Context

The Cloud Platform CLI Tool is used for various tasks, such as generating namespace files and running Terraform. Although useful, there are other ways in which these tasks can be achieved without the need for a separate tool which we need to maintain.

### Decision

We will decommission the CLI Tool.

### Consequences

- We will build new functionality to replace the existing tool
- We will follow existing patterns where possible, eg Modernisation Platform use GitHub Actions to generate user files

## 42. Use Modernisation Platform accounts

Date: 2026-01-02

### Status

✅ Accepted

### Context

The Cloud Platform currently runs in a single AWS account. This was fine whilst the platform was smaller, but we are now hitting multiple AWS limits and the risk associated with blast radius of a single account grows as more services are hosted in there.

AWS accounts for the MoJ are now provisioned via the Modernisation Platform, independant AWS accounts such as the current Cloud Platform account are not part of the strategic vision of all AWS accounts being part of strategic platforms.

### Decision

When moving the Cloud Platform to a multi cluster architecture we will create multiple new accounts in the Modernisation Platform. The old Cloud Platform AWS account will then be decommissioned or migrated into the Modernisation Platform (decision to be made depending on if there are resources which cannot be migrated).

We will use an AWS account per live and non-live clusters (as per ADR 36 Multi Cluster decision).

### Consequences

- We will use the Modernisation Platform security baselines
- We will use the Modernisation Platform SSO for engineer access
- We will use the Modernisation deployment pipelines where possible
- We will use other Modernisation provided services where possible

## 43. New Cloud Platform CIDR ranges

Date: 2026-02-13

### Status

✅ Accepted

### Context

To build the new live and nonlive clusters we need to use an RFC 1918 CIDR range that is unique so that we can route traffic from and to other areas of the MoJ via the MoJ Transit Gateway.

### Decision

We have been allocated the following CIDR ranges from the MoJ Networking team:

Code: 10.41.0.0/16 ⏎ 10.195.0.0/16

These are recoreded in the MoJ IPAM solution. More details can be found [here](https://justiceuk.sharepoint.com/:f:/r/sites/CloudPlatform/Shared%20Documents/Cloud%20Platform/CIDR%20Range%20allocations?csf=1&web=1&e=FOyrbd)

### Consequences

- We will use the above CIDR ranges for the new cluster

## 44. New Platform Name

Date: 2026-03-26

### Status

✅ Accepted

### Context

We are rebuilding the cluster in the Modernisation Platform. For a period of time we will have two platforms running. This creates naming issues with code, DNS, terraform modules and user guidance.

### Decision

We will call the new platform the "Container Platform".

### Consequences

- We will refer to the new platform as the Container Platform
- We will create a new set of user documentation for the container platform
- We will register a new subdomain for `container-platform` and use that for the new platform DNS
- Modules for the new platform will be named with the format `container-platform-terraform`
- The team name will remain as "Cloud Platform", it is just the cluster platform product name that is changing.
- This gives us the option to support other types of platforms with different technologies if the primary technology choice changes

## 45. Use a Private EKS Endpoint

Date: 2026-04-02

### Status

✅ Accepted

### Context

The cluster currently uses a public EKS endpoint, although there is robust authentication in place, there is always a risk if something is exposed on the public internet.  AWS best practice recommends to keep EKS endpoints private.

### Decision

The EKS endpoint will be private. This increases cluster security and follows best practice. It also aligns with other changes we want to make, such as using GitOps and holding all container images in ECR on the platform.

### Consequences

- The EKS endpoint will no longer be publicly accessible.
- We will need to provide a method of access for engineers connecting to the endpoint, this will be via VPN in the first instance, with a bastion accessed via SSM as a break glass measure.
- We will need traffic to our EKS endpoints to be routed via the Global Protect VPN.
- We will need to set up a Bastion, likely using the [Modernisation Platform Bastion module](https://github.com/ministryofjustice/modernisation-platform-terraform-bastion-linux)
- We will no longer allow external connections to the cluster endpoint.
- We will manage our deployments via GitOps. (Potentially ArgoCD)

## 46. Use ECR for all User Images

Date: 2026-04-02

### Status

✅ Accepted

### Context

We currently allow users to host their Docker images anywhere, this has some implications:

- We can't scan images until they are already deployed
- We need to allow external deployment pipelines to access the cluster endpoint
- We can't block images with vulnerabilities
- We can't redeploy user images in a disaster scenario

### Decision

All user images will be hosted in ECR in the Container Platform

### Consequences

- Users will need to change their deployment patterns
- We will need to develop new deployment patterns for users (eg GitOps)

## 47. Use Karpenter For Scaling

Date: 2026-04-21

### Status

✅ Accepted

### Context

The Cloud Platform Team [investigated Karpenter as the technology solution for scaling](https://github.com/ministryofjustice/cloud-platform/issues/8009) during the build of `Container Platform`. We installed and tested **Karpenter**. We [compared Karpenter](https://justiceuk-my.sharepoint.com/:w:/r/personal/dan_criddle_justice_gov_uk/Documents/CP3%20Auto%20Scaling%20Karpenter%20%20Cluster%20Auto%20Scaler.docx?d=w75429c2098ca4980ae8a5151ff211fd1&csf=1&web=1&e=r7FJZF) with **Cluster Auto Scaler** and **EKS Auto Mode**. Testing was successful.

Testing was carried out on `Modernisation Platform` running on **AWS**. It is assumed the cloud provider being used for `Container Platform` will continue to be **AWS**.

### Decision

We will use **Karpenter** as the primary scaling solution for `Container Platform`.

### Consequences

- Scaling is event-driven via direct EC2 Fleet API calls
- User workloads will not run in node groups (**Karpenter** runs outside of node groups, picking instance types dynamically)
- Scaling should occur faster than in `Cloud Platform`
- Node consolidation is more aggressive
- We need to come up with a list of acceptable AWS Instance types and limit to that
- We need to perform tuning and testing with **Karpetner**
- We need to ensure security - see [Karpenter Threat Model](https://karpenter.sh/docs/reference/threat-model/)
- Although it's not our primary use-case **Cluster Auto Scaler** could still run alongside **Karpenter** if needed

## 48. Per Business Unit Clusters

Date: 2026-06-05

### Status

✅ Accepted

### Context

Decision 036 reduces the blast radius with non live and live clusters, but this still leaves the noisy neighbour problem and potential security threats traversing business units.

### Decision

We will give a non-live and a live cluster for each business unit.

### Consequences

- Clusters will be isolated by business unit
- Clusters will be built from the same code so that they are identical to ease maintenance and troubleshooting.
- We will upgrade/add features to all non-live clusters before live clusters, reducing risk.
- Configuration between clusters will be largely identical to ease maintenance and troubleshooting.
- Blast radius will be reduced significately.
- We will need to NAT cluster IPs to ensure we have enough address space.
- Access to clusters and cluster accounts will be achieved with AWS Identity Center.
- Infrastructure and Application pipelines will need to be designed and built to push changes through in the desired order.

## 49. Use Cluster Accounts for Resources

Date: 2026-06-05

### Status

✅ Accepted

### Context

We will need somewhere to put user AWS resources.

### Options

- 1. Use the per business unit cluster accounts - Less AWS accounts and associated overhead, apps sit next to resources, blast radius is limited to business unit. Recommend approach by AWS.
- 2. Use a new AWS non-live and live resources accounts - More overhead, blast radius is still large.
- 3. User new per buiness unit resources accounts - Much more over head, increased distance between app and resouces, good isolation.

### Decision

Option 1 - We will use the cluster accounts for AWS resources.  This is a good balance between limiting blast radius and keeping the apps close to the resources.

### Consequences

- We need to ensure we have enough IPs in the cluster accounts for existing services and growth.

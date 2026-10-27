# GOV.UK Infrastructure Architecture Decision Records

## 1. Record architecture decisions

Date: 2021-08-10

### Status

Accepted

### Context

We need to record the architectural decisions made on this project.

### Decision

We will use Architecture Decision Records (ADRs), as [described by Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

### Consequences

Read Michael Nygard's article for the consequences for choosing to keep Architecture Decision Records. For a lightweight ADR tool set, see [Nat Pryce's `adr-tools`](https://github.com/npryce/adr-tools).

## 2. Use `aws-eks` Terraform module

Date: 2021-08-10

### Status

Accepted

### Context

A fully configured Elastic Kubernetes Service (EKS) cluster requires many AWS resources and a lot of configuration. Defining each resource in our own Terraform module maximises flexibility but also requires a significant level of effort. We could instead make use of the [existing Terraform registry EKS module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest) to optimise for speed of delivery.

### Decision

Adopt the [existing Terraform registry EKS module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest).

### Consequences

We can define fully configured EKS clusters quickly and easily, because many module defaults will be fine for our purposes for the foreseeable future.

The EKS module has comprehensive support for many of the options for EKS cluster config (e.g. worker node types). This will allow us to make changes more easily, and to experiment with different options quickly.

It is possible that we will in future discover some areas of the module that don't work for our needs. Potential options in that instance include contributing to the module, forking it, or moving to our own module (likely with large chunks of code taken from the EKS module).

We must be careful to avoid any errors and issues caused by the module's default use of a Terraform `kubernetes` provider. The behaviour of providers derived from other providers' resources is non-deterministic and can lead to intermittent and unpredictable issues - see [the warning in the Kubernetes provider docs](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs#stacking-with-managed-kubernetes-cluster-resources). We will cover the approach for handling this limitation in a subsequent ADR.

## 3. Split Terraform state into separate AWS cluster and Kubernetes resource phases

Date: 2021-08-11

### Status

Accepted

### Context

Our Terraform will require the use of at least the `aws` and `kubernetes` providers. Elastic Kubernetes Service (EKS) infrastructure resources will get defined with the `aws` provider, and in-cluster resources and configuration will get defined with the `kubernetes` provider. The `kubernetes` provider requires arguments that are dependent on AWS resource outputs, so a naïve implementation would look like this:

Code: provider "aws" { ⏎ region = var.region ⏎ } ⏎ resource "aws_eks_cluster" "cluster" { ⏎ ... ⏎ } ⏎ provider "kubernetes" { ⏎ host                   = aws_eks_cluster.cluster.endpoint ⏎ cluster_ca_certificate = base64decode(aws_eks_cluster.cluster.certificate_authority.0.data) ⏎ token                  = aws_eks_cluster.cluster.token ⏎ }

Terraform providers are not handled as nodes in the Terraform plan graph, so Terraform cannot guarantee that AWS resources are fully created at the point that it configures the `kubernetes` provider. This will lead to non-deterministic behaviour and race conditions, where the values needed by the `kubernetes` provider are not available at the time it gets initialised. Because of this, [Terraform providers should only use config values they know ahead of time](https://www.terraform.io/docs/language/providers/configuration.html#provider-configuration-1).

### Decision

Split Terraform resources into two separate states and phases:

- 1. `cluster-infrastructure` - EKS cluster and associated AWS resources. We do not define a `kubernetes` provider in this root.
- 2. `cluster-services` - Kubernetes resources (for example, ingress controllers) and in-cluster configuration (for example, `aws-auth` `ConfigMaps`), with a `kubernetes` provider configured using values from a Terraform remote state resource. It will be applied after `cluster-infrastructure`. We will not define an `aws` provider in this root, unless we identify a need to access AWS data sources for use in Kubernetes resources (for example, getting the current AWS region).

These names are placeholders, and we will select permanent ones outside of this ADR.

### Consequences

We must set the [EKS module's `manage_aws_auth` input variable](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest) to `false` to prevent the module attempting to create `ConfigMap` objects for AWS authentication.

This should also prevent failures when tearing down EKS clusters with deployed workloads. Ingress controllers and Kubernetes `Service` objects commonly provision AWS load balancers that Terraform does not know about, and therefore cannot include in a destruction plan. It is not possible to delete an EKS cluster to which other AWS resources still point.

This decision also introduces a clear boundary and separation of concerns between Kubernetes cluster provisioning, and in-cluster resources and configuration. This is an important and useful separation to enforce, because it keeps the largely generic cluster infrastructure separate from the GOV.UK-specific configuration and supporting services. This, in principle, provides a path to switching from an EKS cluster to any other Kubernetes cluster in any environment. It also provides a baseline EKS cluster that we could use for other non-GOV.UK purposes in the future.

## 4. Use AWS Load Balancer Controller for edge traffic services

<!-- "AWS Load Balancer Controller" is correctly capitalised as a proper noun --> <!-- vale RedHat.Headings = YES -->

Date: 2021-08-12

### Status

Accepted

### Context

We require a method of managing and directing external internet traffic into the cluster. Kubernetes provides [several options for handling inbound traffic](https://medium.com/google-cloud/kubernetes-nodeport-vs-loadbalancer-vs-ingress-when-should-i-use-what-922f010849e0).

We do not want to expose the cluster directly to the internet, so we require an AWS load balancer in front of the cluster. The load balancer must support TLS termination and integration with our DNS provider (AWS Route 53).

Historically, Kubernetes has supported provisioning of Application Load Balancers (ALBs) and Network Load Balancers (NLBs) for `Service` resources of `type=LoadBalancer` using the in-tree (built-in) [AWS cloud provider](https://github.com/kubernetes/cloud-provider-aws).`Ingress` resources have always been supported by out-of-tree controllers required.

Built-in cloud providers are now [considered deprecated overall, in favour of out-of-tree providers](https://kubernetes.io/blog/2019/04/17/the-future-of-cloud-providers-in-kubernetes/), so users are now required to use an [Ingress Controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/) with support for `Service` resources.

The primary, and recommended, ingress controller for AWS' Elastic Kubernetes Service (EKS) is the [AWS Load Balancer Controller](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html), which can provision and manage [ALBs for `Ingress` resources and NLBs for `Service` resources](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.2/#aws-load-balancer-controller).

We must also consider how Kubernetes edge services and AWS load balancers will interact with the existing [GOV.UK Router service](https://github.com/alphagov/router), because there is significant overlap in their functionality and responsibilities. This will require further investigation, so we should be able to use both `Ingress` and `Service` Kubernetes resources. This will ensure we have the flexibility to support a wide range of use cases in the immediate term: layer 4 and layer 7 traffic, name-based routing, HTTP-to-HTTPS redirection.

### Decision

Use the [AWS Load Balancer Controller](https://github.com/kubernetes-sigs/aws-load-balancer-controller).

### Consequences

The AWS Load Balancer Controller supports TLS certificates with AWS Certificate Manager only. A future ADR will cover the way in which we use AWS Certificate Manager.

The load balancer controller does not handle DNS for declared ingress host names. A future ADR will cover a solution to this.

We will need to establish an appropriate Application and Network Load Balancer topography: how many load balancers routing to where. By default the controller will provision one load balancer per `Ingress` resource, which might not be what we want. <!-- vale RedHat.PassiveVoice = NO --> Ingresses [can be grouped](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.2/guide/ingress/annotations/#ingressgroup), however. <!-- "be grouped" is the correct verbiage. It's a valid use of passive voice --> <!-- vale RedHat.PassiveVoice = YES -->

The load balancer controller supports [AWS Web Application Firewall and Shield](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.2/guide/ingress/annotations/#addons), both of which are currently in use on GOV.UK.

<!-- vale RedHat.PassiveVoice = NO --> <!-- vale RedHat.SentenceLength = NO -->

We must also investigate access control for Ingress rules, likely in conjunction with Kubernetes `namespace` usage. If all of GOV.UK is deployed into a single namespace, and many users or service accounts have the same level of access to `Ingress` objects, then user or process for component A could modify or destroy ingress rules for component B.

<!-- This paragraph makes sense and is not too long. It's just longer than the usual rule would allow for --> <!-- vale RedHat.PassiveVoice = YES --> <!-- vale RedHat.SentenceLength = YES -->

## 5. Use AWS Elastic Kubernetes Service (EKS) managed node groups

<!-- Heading contains proper nouns, so sentence casing is not appropriate --> <!-- vale RedHat.Headings = YES -->

Date: 2021-08-13

### Status

Accepted

### Context

EKS supports three different types of EKS worker node groups: [managed, self-managed, and Fargate](https://docs.aws.amazon.com/eks/latest/userguide/eks-compute.html). The three options are not mutually exclusive. A single EKS cluster can schedule pods onto any combination of the three, with support for many managed and self-managed node groups in a single cluster.

Managed and self-managed node groups are both implemented as EC2 instances within autoscaling groups, with all the configuration options that this implies: security groups, custom AMIs, instance types, and so on. Fargate is a managed service, so there are fewer configuration options available, and less management overhead.

A major consideration is the implications for [cluster upgrades](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html). Kubernetes has a 4-month release cycle, so upgrades will be relatively frequent. We will require a robust and mature node upgrade process, given the potentially destructive nature of worker updates.

At this stage our requirements for worker nodes are not fully known, so maintaining flexibility is important.

The functional capabilities of nodes in managed and self-managed node groups are equivalent, whereas Fargate places some limitations on pod and cluster capabilities. For example, it cannot run `DaemonSets`, specify an alternative Container Network Interface provider, or attach persistent Elastic Block Store (EBS) volumes to pods.

The main distinction between managed and self-managed node groups is the node upgrade process. [Managed node groups handle graceful upgrades largely automatically](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html), whereas self-managed groups would require us to [orchestrate the update process ourselves](https://docs.aws.amazon.com/eks/latest/userguide/migrate-stack.html).

### Decision

Use [managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html).

### Consequences

We retain maximum flexibility over node configuration without having to handle the low-level details and complexity of rolling out node updates in a running cluster.

Choosing managed node groups does not rule out the use of self-managed node groups, Fargate, or a mix of all three, in the future. If we discover that either alternative better fits our needs, introducing self-managed or Fargate node-group would be a purely additive process. We would not have to discard any significant work on managed node groups.

## 6. Use Helm for application package management

Date: 2021-08-16

### Status

Accepted

### Context

We require something more sophisticated than handcrafted YAML when defining an application's Kubernetes resources. We need to this to ensure that we can define applications one time, and deploy them to different targets with differing configurations. At a high level, we require a means to define an application's Kubernetes resources as an installable package, with configuration options passed in at deploy time.

There are many options for packaging Kubernetes applications, including but not limited to:

<!-- vale Vale.Spelling = NO --> <!-- vale RedHat.Spelling = NO -->

- [Helm](https://helm.sh)
- [Terraform](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs)
- [Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
- [Pulumi](https://www.pulumi.com/docs/intro/cloud-providers/kubernetes/#pulumi-kubernetes-provider)
- [Skaffold](https://skaffold.dev)

<!-- Product names have funny spellings --> <!-- vale Vale.Spelling = YES --> <!-- vale RedHat.Spelling = YES -->

We are currently using Terraform for AWS infrastructure management, and we should maintain a strict separation of concerns between managing cloud infrastructure and the software applications that run on top. Using a single tool for both will inevitably lead to blurred lines between them. In addition, [Terraform's Kubernetes support is still quite new](https://www.hashicorp.com/blog/beta-support-for-crds-in-the-terraform-provider-for-kubernetes), and can lag behind Kubernetes itself.

Although the main Kubernetes project adopted Kustomize, the decision has [not been without controversy](https://goteleport.com/blog/kubernetes-kustomize-kep-kerfuffle/). Kustomize has not yet seen wide adoption within the industry, and offers little beyond the basic functions of interpolating values into YAML files.

Helm by comparison has widespread industry adoption, a [large number of existing packages](https://artifacthub.io/packages/search), and widespread support in the wider devops and development ecosystem. For example [GitHub Actions](https://github.com/helm/chart-releaser-action), [CircleCI Orb](https://circleci.com/developer/orbs/orb/circleci/helm),[Visual Studio Code extension](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools), and the [Terraform provider](https://registry.terraform.io/providers/hashicorp/helm/latest/docs).

### Decision

Use Helm v3+.

### Consequences

We can make use of existing Helm charts for supporting tools and services:

- [AWS Load Balancer Controller](https://artifacthub.io/packages/helm/aws/aws-load-balancer-controller)
- [Prometheus and Grafana](https://artifacthub.io/packages/helm/prometheus-community/kube-prometheus-stack)
- [Fluentd](https://artifacthub.io/packages/helm/bitnami/fluentd)

While not required at this stage, we will likely want to consider introducing a [Helm chart repository](https://helm.sh/docs/topics/chart_repository/) at some stage in the future.

<!-- vale RedHat.PassiveVoice = NO --> Helm provides a [release history](https://helm.sh/docs/helm/helm_history/) for an installed chart, and support for [rolling back to earlier releases](https://helm.sh/docs/helm/helm_rollback/). Care must be taken when rolling back an application with a dependency on database migrations, however.

Helm charts [are versioned](https://helm.sh/docs/topics/charts/#charts-and-versioning) entirely separately from the _application_ version. Care must be taken to avoid confusion between the two, particularly when communicating with chart authors in development teams. <!-- Valid uses of passive voice --> <!-- vale RedHat.PassiveVoice = YES -->

Helm adds Go templates to YAML, and [YAML](https://docs.saltproject.io/en/latest/topics/troubleshooting/yaml_idiosyncrasies.html) [is](https://www.elastic.co/guide/en/beats/libbeat/current/config-file-format-tips.html) [still](https://www.arp242.net/yaml-config.html) [YAML](https://speakerdeck.com/xeraa/yaml-considered-harmful). The wisdom of applying text templating to JSON-derived data structures aside, we should be conscious of YAML idiosyncrasies when authoring charts or defining values.

<!-- vale Vale.Spelling = NO --> <!-- vale RedHat.Spelling = NO --> Helm and the many other options are not mutually exclusive, so our adoption of Helm does not prevent the use of any other tools, now or in the future. If development teams want to adopt Kustomize or Skaffold instead there is nothing in principle to prevent that. <!-- Product names have funny spellings --> <!-- vale Vale.Spelling = YES --> <!-- vale RedHat.Spelling = YES -->

## 7. Use Fluent Bit, Elasticsearch and Kibana for application logs

<!-- Title contains proper nouns. Sentence casing irrelevant --> <!-- vale RedHat.Headings = YES -->

Date: 2021-08-16

### Status

Deprecated (no superseding ADR)

### Context

#### Log collection and forwarding

Application containers should output their logs as [`stdout`/`stderr` streams](https://12factor.net/logs), which an aggregator can forward to a single log store. These logs should be searchable, filterable, and appropriately tagged.

There are two broad approaches to log collection and forwarding in Kubernetes

- Run a [sidecar container](https://kubernetes.io/docs/concepts/cluster-administration/logging/#sidecar-container-with-logging-agent) within each `Pod` to pick up the application's logs from a file or socket and forward them on (this is the only available option with [Elastic Kubernetes Service (EKS) Fargate, although partially managed by AWS](https://docs.aws.amazon.com/eks/latest/userguide/fargate-logging.html))
- Run a log collection and forwarder agent on [each node as a `DaemonSet`](https://kubernetes.io/docs/concepts/cluster-administration/logging/#using-a-node-logging-agent)

We must have logging as a service and enable it by default for all containers, so the sidecar pattern does not meet our needs.

To make application logs searchable and navigable, we require the logging agent to annotate and index logs with Kubernetes cluster metadata (namespace, pod name, labels, and so on).

The most commonly used logging agents for Kubernetes are: [Fluentd](https://www.fluentd.org) and [Fluent Bit](https://fluentbit.io). Fluent Bit is a successor to Fluentd, and aims to be more lightweight and offer better performance, but has a smaller plugin ecosystem than Fluentd.

#### Log storage and UI

We must store our logs somewhere, with a browser-based UI for searching, filtering, and browsing. There are many options in the space, but the most common option is [Elasticsearch and Kibana](https://www.elastic.co/what-is/elk-stack).

It is possible that we will ultimately push logs to a GDS-wide central log store, but we should deploy something ourselves in the short term. Doing so will ensure we have a usable logging service for our users sooner rather than later, and get familiar with the details of logging within Kubernetes ourselves.

For now, the obvious choice is Elasticsearch and Kibana, due to their extensive support for this use case and in this ecosystem.

### Decision

Use a **Fluent Bit** `DaemonsSet` with AWS Elasticsearch Service.

### Consequences

Fluent Bit is a lighter and faster alternative to Fluentd, with first-class Kubernetes support. It does however have a smaller plugin ecosystem, although we are unlikely to need any exotic plugins.

Fluent Bit and Fluentd are largely drop-in replacements for each other, so we can quickly and easily change logging agents if necessary.

Fluent Bit can be quickly deployed with little to no configuration by using the [official Helm chart](https://github.com/fluent/helm-charts).

AWS Elasticsearch Service provides both [Elasticsearch itself, plus Kibana](https://aws.amazon.com/elasticsearch-service/features/).

We must restrict access to Kibana with authentication, ideally with corporate identities. We must explore appropriate options for this, for example AWS SSO, or Cognito. Similarly, we might also require authorization and segregation within Elasticsearch itself.

This ADR covers application-level logging only, not cluster control plane or node or `kubelet` logs. A future ADR will be cover that.

## 8. Use external-secrets for secrets storage

Date: 2021-08-26

### Status

Accepted

### Context

We want to make use of AWS SecretsManager for secrets storage, rather than relying solely on Kubernetes secrets. We want to do this because we want the ability to reconstitute the full state of a running cluster from an external source of truth. In most cases the external source of truth is a Git repository, but there are significant challenges and pain points when managing sensitive config in Git repositories. These pains are the driver for using SecretsManager.

We must maintain end-to-end encryption of secrets, up until the point a running container uses a secret, where Kubernetes must necessarily decrypt the secret for use.

We must be able to enforce access control on secrets, following the principle of least privilege.

We must be able to support rotation of secrets in AWS SecretsManager, where a change of value in AWS is automatically propagated to services in the cluster.

Kubernetes should expose secrets to pods as `Secret` resources, to allow the use of standard patterns and existing third-party Kubernetes projects (primarily Helm charts). The use of externally-managed secrets should have a minimal impact on development teams, and Helm chart and Kubernetes resource authors, because we will manage the SecretsManager integration at a cluster level.

Several projects exist for AWS SecretsManager integration with Kubernetes Secrets, the most notable being:

- [Secrets Store Container Storage Interface (CSI) Driver](https://secrets-store-csi-driver.sigs.k8s.io)
- [`external-secrets`](https://github.com/external-secrets/external-secrets)
- [`kubernetes-external-secrets`](https://github.com/external-secrets/kubernetes-external-secrets)

Secrets Store CSI is a [Kubernetes Special Interest Group (SIG)](https://github.com/kubernetes/community/blob/master/sig-list.md) project. It aims to implement external secrets in Kubernetes clusters by using the [Container Storage Interface](https://kubernetes.io/blog/2019/01/15/container-storage-interface-ga/), a standard for exposing file and block interfaces to containers.

<!-- vale RedHat.PassiveVoice = NO --> <!-- vale RedHat.SentenceLength = NO --> `external-secrets` and `kubernetes-external-secrets` are closely-related projects that have been brought together as part of the [external-secrets](https://github.com/external-secrets) GitHub org, which has worked to unify many projects in this space and create a [single specification for an external secrets Custom Resource Definition](https://github.com/external-secrets/crd-spec/blob/main/Spec.md). <!-- Valid use of passive voice in this long sentence --> <!-- vale RedHat.SentenceLength = YES --> <!-- vale RedHat.PassiveVoice = YES -->

`external-secrets` is the successor project to `kubernetes-external-secrets`, which rewrites the [Kubernetes Operator](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) in Go rather than JavaScript, and adopts the standardised Custom Resource Definition (CRD). It also changes the resource object model to separate using secrets in the application, and the specific access and authentication and authorization implementation for a given external secret backend. Both projects support AWS SecretsManager, HashiCorp Vault, and Google Cloud Platform and Azure equivalents. The project maintainers view `kubernetes-external-secrets` as on a deprecation path, and `external-secrets` is currently classed as alpha:

> [Kubernetes External Secrets]: a very popular solution that came from within Godaddy and was written in JS and > supports a lot of providers (but will be deprecated) > > [External Secrets]: New solution written in golang, aspires to support all the same providers, but we are still > working on getting most of the providers stable and out of alpha. Eventually, the idea is to substitute KES. Anyways the > migration is pretty much like @Flydiverny said since retro-compatibility with original solutions was not something that > we aimed for. Completely new CRD and all that.

(from [Kubernetes Slack](https://kubernetes.slack.com/archives/C017BF84G2Y/p1626186324108900?thread_ts=1626104012.105800&cid=C017BF84G2Y))

We have created proofs of concept for all three options:

- 1. **Secrets Store CSI** - works, but relatively complex to get up and running. Secrets rotation and syncing with Kubernetes `Secrets` currently experimental/alpha. The use of CSI volumes as an abstraction [requires that secrets get mounted as a volume](https://secrets-store-csi-driver.sigs.k8s.io/topics/sync-as-kubernetes-secret.html) on disk even when secrets are only consumed as environment variables by containers. Secrets volume definition in `Pods` and `Deployments` is quite verbose and something of a leaky abstraction, because it must specify the CSI driver and volume attributes. Overall CSI feels like the wrong abstraction for external secret stores, because they are fundamentally neither file nor block storage.
- 2. **`kubernetes-external-secrets`** - Quick and easy to get up and running and simple to use within an application it requires only one resource: `ExternalSecret`. Works as expected with [IAM Roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html). In-cluster secrets access control is [relatively basic and coarse-grained](https://github.com/external-secrets/kubernetes-external-secrets#scoping-access). Does not support a highly-available deployment (replicas) without the risk of excessive API calls or race conditions.
- 3. **`external-secrets`** - More complex to get up and running than `kubernetes-external-secrets`, and less so than Secrets Store CSI. Documentation is somewhat thin, although [the`external-secrets` API spec](https://external-secrets.io/spec/) is comprehensive. Supports [a few modes of operation for multi-tenancy](https://external-secrets.io/guides-multi-tenancy/) and access control. Project is still in a relatively early stage, so APIs might change. Supports highly available deployments via leadership election.

While multi-tenancy is not a primary concern at this stage, we might discover a need for some level of access control and segregation as we introduce more applications.

### Decision

Use [**`external-secrets`**](https://external-secrets.io).

While `kubernetes-external-secrets` is more mature and slightly simpler to deploy and use, it is also on a deprecation path, with no plans for a migration path to `external-secrets`.

`external-secrets` is less mature and slightly more complex, but not significantly so, and proof of concept tests did not raise any significant issues.

Given that the SIG have destined `kubernetes-external-secrets` for deprecation, we should invest our time in the future-facing project, even though it is still in a relatively early stage.

### Consequences

We might find more than average numbers of bugs and changes as the project is in a relatively early stage.

We must establish the structure of secrets in AWS, and IAM roles and access patterns. We will cover them in a future ADR.

To maintain end-to-end encryption of secrets, we will enable [Key Management Service encryption for Kubernetes Secrets](https://aws.amazon.com/about-aws/whats-new/2020/03/amazon-eks-adds-envelope-encryption-for-secrets-with-aws-kms/).

Secret rotation does not automatically restart secrets-consuming `Pods`; this is true of all three projects. We would require a separate component [such as `Reloader`](https://github.com/stakater/Reloader) to implement this.

## 9. Use `external-dns` for DNS record management

Date: 2021-08-27

### Status

Accepted

### Context

We want to be able to manage DNS records for Kubernetes `Ingress` and `Service type=Loadbalancer` resources declaratively with Kubernetes resources, so that we avoid the overhead and brittleness of manual DNS management with Terraform.

[`external-dns`](https://github.com/kubernetes-sigs/external-dns) is the primary project in this space and gives us everything we need; Route53 integration, support for all AWS load balancer types, integration with [`alb-ingress-controller`](https://github.com/kubernetes-sigs/external-dns/blob/master/docs/tutorials/alb-ingress.md) and [IAM Roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) support.

### Decision

Use [`external-dns`](https://github.com/kubernetes-sigs/external-dns).

### Consequences

We can install it with [a Helm chart](https://artifacthub.io/packages/helm/bitnami/external-dns).

`Ingress` and `Service` resources can configure a DNS record with a simple annotation:

Code: apiVersion: networking.k8s.io/v1 ⏎ kind: Ingress ⏎ metadata: ⏎ annotations: ⏎ external-dns.alpha.kubernetes.io/hostname: foo.test.govuk.digital

## 10. Use Dex IdP for user web authentication

Date: 2021-12-01

### Status

Accepted

### Context

We want to implement user authentication on the monitoring stack's web applications (Grafana, Prometheus, Alertmanager).

We also want to use GitHub as the identity provider, because that provides a means for us to control access based on GDS GitHub organisation and team membership. The alternative option, GSuite, does not have the granular role or group structure that we would require to effectively control access, and implementing it be out of scope for us. It would likely replicate the GitHub group and team structure that currently exists.

Grafana supports many authentication methods, including [GitHub OAuth2](https://grafana.com/docs/grafana/latest/auth/github/) and [Open Identity Connect (OIDC) through generic OAuth2](https://grafana.com/docs/grafana/latest/auth/generic-oauth/).

Prometheus and Alertmanager do not support any form of web-based user authentication, so authentication must happen at a proxy or load balancer in front of the application.

We are currently using Application Load Balancers (ALB) in front of Prometheus and Alertmanager, from the [AWS Load Balancer Controller](0004-use-aws-load-balancer-controller-for-edge-traffic-services.md), which supports [authentication with AWS Cognito or OIDC-compliant identity providers](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.3/guide/ingress/annotations/#authentication).

GitHub as an identity provider does not support OIDC, only OAuth2, so we cannot use it for ALB authentication. AWS Cognito [does not support OAuth2, only OIDC](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html), so we cannot use it with GitHub as an identity provider.

ArgoCD, our current CD tool, also [implements authentication with OIDC](https://argo-cd.readthedocs.io/en/stable/operator-manual/user-management/#existing-oidc-provider), and [includes an OIDC-compliant identity broker](https://argoproj.github.io/argo-workflows/argo-server-sso-argocd/): [Dex](https://dexidp.io).

In summary, OIDC is the only authentication protocol supported universally by both our current web-based UIs that have authentication built-in, and by Application Load Balancers for apps that do not. GitHub however does not offer an OIDC-compliant identity provider.

### Decision

Use [Dex](https://dexidp.io) as a Single Sign-On (SSO) service and identity provider for all web-based user authentication. This is strictly for use with user-facing, web-based cluster services such as monitoring and CI/CD tools. We should not used it for any other purposes, such as AWS or Kubernetes authentication.

### Consequences

We will have an SSO service and consistent identity provider for all user-facing platform UIs, now and in the future. This will give us a single integration with the underlying identity provider, and only one component will need a configuration change in the event that the identity provider changes in the future.

Dex is currently deployed as a component of the larger Argo service. It will now be a shared platform service, so we will remove it in favour of a standalone Dex [Helm chart installation](https://github.com/dexidp/helm-charts).

Being an SSO service, Dex is also a single point of failure and a clear potential target for attack. Therefore, Dex must be highly available, secure, and covered in the scope of penetration testing.

## 11. Use AWS Graviton (ARM) for compute instances

<!-- Heading contains proper nouns --> <!-- vale RedHat.Headings = YES -->

Date: 2025-03-03

### Status

Accepted

### Context

We want to switch our compute instances over to AWS Graviton-powered instance types.

<!-- vale RedHat.PassiveVoice = NO --> The majority of engineers on GOV.UK (and the wider GDS) are using GDS-issued MacBooks, which have Apple Silicon CPUs that are based on the ARM CPU architecture. Switching our Production (and non-Production) workloads to use the same architecture would ensure that what we develop and test on locally and in non-Prod matches what we run in Production. <!-- "are based on" is a valid sure of passive voice --> <!-- vale RedHat.PassiveVoice = YES -->

AWS Graviton-powered compute instances (usually denoted with a "g", e.g. `M7g`, `R7g`, and so on) are typically cheaper than their AMD (`M7a`, `R7a`) or Intel (`M7i`, `R7i`) counterparts. This will reduce running costs. ARM-based CPUs typically consume less power and have a more efficient total power draw versus AMD and Intel equivalents, and are potentially better for our carbon footprint.

Switching to AWS Elastic Kubernetes Service (EKS) has made it easier for us to support different CPU architectures side-by-side and to migrate our workloads gracefully with no downtime.

If we need to run x86_64 workloads again in the future, we can easily support this side-by-side with Graviton workloads, thanks to Kubernetes being architecture-agnostic.

### Decision

- 1. Update our CI/CD to build all GOV.UK app images with ARM support
- 2. Update our EKS node groups to add Graviton EC2 instances to our clusters
- 3. Instruct Kubernetes to deploy only ARM-architecture images
- 4. Scale our x86_64 (Intel) node groups down to zero.

### Consequences

We will adopt an ARM-first approach for our software development and unify our architectures in Development, non-Production and Production environments. We will retain the flexibility to continue to support x86_64 workloads should the need arise in the future.

#### Cost Savings

The cost saving per-instance is about 15% when stepping from `m6i` to `m7g` instances of the same "size". However, the benefits are potentially more significant when combined with more efficient compute, right-sizing efforts and committing to the correct AWS savings plans.

Further, making improvements to our workload resource requests and limits has allowed us to right-size our infrastructure and not need to over-provision our compute instances. This has resulted in a 55% cost saving when combined with our switch to Graviton hardware. Savings Plans will improve our savings further.

The GOV.UK Platform Engineering team can produce calculations on-request.

### Summary

Following the decision to switch all of GOV.UK over to Graviton, GOV.UK will:

- Use the same CPU architecture across Development and Production environments
- Save on compute costs and be more efficient to run
- Be flexible, because we retain the capability to run traditional x86 workloads

## 12. Non-GOV.UK domain policy

Date: 2025-05-06

### Status

Accepted

### Definitions

This proposal uses the [RFC2119](https://www.ietf.org/rfc/rfc2119.txt) standard for definitions of MUST, MUST NOT and MAY.

Definitions:

- "Authenticated": through an authentication method such as `Signon`, through [basic access authentication](https://en.wikipedia.org/wiki/Basic_access_authentication), or similar
- "Non-GOV.UK domain": a domain that does not end in `gov.uk`, such as `govuk.digital` or `govuk-internal.digital`. We consider `assets.publishing.service.gov.uk` to be a GOV.UK domain.

### Context

It is dangerous to have a Non-GOV.UK domain that is publicly accessible, without an authentication layer, and does either of the following:

- 1. Looks like a GOV.UK site
- 2. Plays any publicly detectable part in serving content to a GOV.UK site

In either case, systems such as [Google's Safe Browsing](https://transparencyreport.google.com/safe-browsing/search), in use by browsers to automatically block requests to dangerous sites, might flag the domain as a phishing site.

At best, this would be an inconvenience, perhaps making it difficult to access internal tooling. At worst, this could cause a major incident, making large parts of GOV.UK inaccessible.

### Proposal

Any web page that lives on a Non-GOV.UK domain, and looks like a page or service on GOV.UK, MUST either be Authenticated or unavailable to the public internet.

Additionally, the serving of any GOV.UK web page or assets MUST NOT use a Non-GOV.UK domain in any publicly detectable part of the request. Some examples of things to avoid:

- 1. Using a Non-GOV.UK domain in the redirect chain for a GOV.UK page or asset.
- 1. Making requests to a Non-GOV.UK domain for metadata associated with a GOV.UK page or asset. For example, a request for a GOV.UK asset triggering a second request for a favicon from a Non-GOV.UK domain.

To be clear, a Non-GOV.UK domain MAY be used in serving GOV.UK pages or assets, provided the domain in question is not publicly detectable. For example, `govuk-internal.digital` MAY be used under the hood to process a request, provided the domain is not exposed to the browser at any point in the request.

## 13. Expose external metrics for Horizontal Pod Autoscaler using Prometheus adapter

<!-- Title contains proper nouns --> <!-- vale RedHat.Headings = YES -->

Date: 2025-06-03

### Status

Accepted

### Context

Kubernetes Horizontal Pod Autoscalers (HPAs) on GOV.UK currently scale only on CPU and memory metrics from `metrics-server`. Several workloads (starting with Chat AI) need to scale on application-level signals, such as a Sidekiq queue backlog length. Kubernetes requires these signals to be available through the `external.metrics.k8s.io` API group.

Prometheus already scrapes the backlog metric (`sidekiq_queue_backlog{job="govuk-chat-worker"}`) in every cluster, but the cluster lacks a component that translates Prometheus data into the `external-metrics` API.

### Decision

- Adopt the **Prometheus Adapter** Helm chart (`prometheus-community/prometheus-adapter`) as the standard way to serve external metrics.
- Deploy the chart in the `monitoring` namespace and manage it with our existing GitOps repository (`govuk-helm-charts`) and Argo CD.
- Create a minimal external-metrics rule set per environment; first rule:

```yaml seriesQuery: 'sidekiq_queue_backlog{job="govuk-chat-worker"}' name: { as: ai_sidekiq_queue_backlog } resources: overrides: namespace: { resource: namespace } metricsQuery: | max(sidekiq_queue_backlog{job="govuk-chat-worker"}) ```

- Roll out progressively: **integration → staging → production**, validating `APIService` health (`Available=True`) and metric availability at each stage. We've only deployed the adapter in integration so far. When we discuss this ADR and approve it, we will proceed with the roll out.
- Keep default rules disabled (`rules.default: false`) to avoid flooding Prometheus with queries.
- Rely on the adapter's native config (`--enable-external-metrics` flag is not needed in v0.12+). The presence of `externalRules:` is enough.

### Consequences

#### Positive

- Application teams can configure HPAs on any Prometheus-exposed metric with a namespace label, unlocking finer-grained, workload-specific scaling.
- Approach is Cloud Native Computing Foundation-standard, requires no custom controllers, and fits our existing fork-less Helm + Argo workflow.
- Adapter pods are lightweight; one replica per cluster adds < 100 MiB memory commitment and negligible CPU.

#### Negatives and risks

- Mis-configured rules can crash the adapter (fatal on invalid `resource` names) and take the `APIService` down.
- *Mitigation:** PR checks and chart tests.
- Additional Prometheus queries every `metricsRelistInterval` (default 1 min).
- **Mitigation:** keep rules focused; monitor Prometheus CPU.
- Production HPAs based on poor signals could over- or under-scale services.
- **Mitigation:** gated roll out, conservative target values, clear run books.

#### Follow-ups

- Add documentation and a snippet showing how to write new `externalRules`.
- Consider bumping adapter replicas to 2 in production for HA.
- Evaluate whether any default resource-metrics support (`kube-top` style) is worth enabling later.

## 14. Replace Terraform Cloud backend with AWS S3

Date: 2025-06-10

### Status

Accepted

### Context

GOV.UK's infrastructure-as‑code currently stores Terraform state in **Terraform Cloud**. We have **93 workspaces** (each with integration, staging, and production environments) and pay a lot for the service.

While Terraform Cloud gives us managed state, variable sets, secret interpolation, and a friendly UI, its cost and proprietary lock‑in are no longer acceptable. A renewal decision is due within six months.

S3‑backed state with S3 native locking has matured, and AWS already meets our security baseline (Server-Side Encryption (SSE) using AWS Key Management Service (KMS), CloudTrail, GuardDuty). We estimate an annual cost of **<£100**, a >99% saving.

### Decision

- **Adopt S3 as the canonical Terraform backend** for all workspaces.
- Provision **one bucket per environment**:
- `govuk-terraform-state-integration`
- `govuk-terraform-state-staging`
- `govuk-terraform-state-production` with versioning, bucket‑level public‑access blocks and SSE‑KMS.
- Retain object versions for **90 days** via an S3 lifecycle rule.
- Manage these resources through a shared `state-backend` Terraform module in `govuk-infrastructure`.
- Example workspace backend block:

```hcl terraform { backend "s3" { bucket         = "govuk-terraform-state-${ var.environment }" key            = "${ path_relative_to_include() }/terraform.tfstate" region         = "eu-west-2" encrypt        = true } } ```

- **Access controls**
- CI role `github-actions-tf` (or *Atlantis*, pending spike) – write + lock.
- Human role `govuk-platform-engineer` – read/write for break‑glass only.
- **Migration plan**: workspace‑by‑workspace, beginning with integration; fallback is to repoint the backend to Terraform Cloud.
- We will cancel the Terraform Cloud subscription once we have migrated all the workspaces; this ADR will move to *Accepted*.

### Consequences

#### Positive

- Reduces infrastructure as code platform spend by ≥99%.
- Removes vendor lock‑in; state lives wholly inside our AWS org.
- Leverages existing AWS security tooling and auditing.
- Aligns with open source, Cloud Native Computing Foundation‑standard workflows.

#### Negatives and risks

- Loss of Terraform Cloud convenience features (run UI, drift detection, cost estimation). *Mitigation:* self‑hosted GitHub Actions runner or Atlantis; `Infracost`; scheduled drift plans.
- Mis‑configured bucket access control lists or KMS access cab expose or corrupt state. *Mitigation:* module tests, CI policy checks, Slack alerts on failed state writes or locks.
- Pipeline‑runner security: anyone with repository write might gain infrastructure access. *Mitigation:* decide between hardened self‑hosted GitHub Actions runners or Atlantis.

#### Follow‑ups

- Complete runner spike and update ADR with chosen solution.
- Automate monthly cost report comparing S3 spend and historical Terraform Cloud invoice.
- Document onboarding steps for new workspaces.

## 15. Maintain a read-only IAM role

Date: 2026-06-16

### Status

Accepted

### Context

We aim to adhere to the principle of least privilege wherever we can. In the particular case of AWS and Kubernetes cluster access we do this by providing a set of IAM and Kubernetes roles. Each role grants the permissions needed for engineers to do routine parts of their jobs. We maintain a separate set of roles with the permissions needed for more destructive or sensitive acts that we more tightly gate access to.

<!-- vale RedHat.TermsWarnings = NO --> Prior to May 2025 we had four roles: `ReadOnly`, `User`, `PowerUser`, and `Admin`. We ran a developer survey and discovered that most users were defaulting to using the `PowerUser` role because `ReadOnly` didn't grant them access to everything they needed. Crucially, it did not grant them access to Amazon Athena. Developers found friction in using the`ReadOnly` role for most of their work, only to find they needed to switch roles to use Athena. In the end, most developers had begun to assume the `PowerUser` role by default, which granted them additional permissions in excess of that they _required_ to do their work. <!-- Linting rule is mistaking "May" as a synonym for "might" instead of the month --> <!-- vale RedHat.TermsWarnings = YES -->

In response to this, we elected to retire the `ReadOnly`, `User`, and `PowerUser`roles in favour of new roles whose granted permissions better reflected those needed by the developers: `Developer`.

We noted that the `Developer` role granted its users the permission to update and delete Kubernetes `Deployment`resources, making it possible to take running applications offline. `Developer` had become the lowest level of privilege available to its users, and we felt that the lowest level of privilege should not be capable of causing a production outage. However, the ability to mutate `Deployment` resources is a valid and useful permission for developers to have.

In June 2025 we reconsidered the need for a `ReadOnly` role.

### Decision

We have decided to reintroduce the `ReadOnly` role to give a fully read-only level of privilege in a number of scenarios:

- 1. Developers wanting to just look about without changing anything,
- 2. Junior/apprentice level roles needing access without the ability to accidentally change anything,
- 3. External people, such as pen testers, needing access to our AWS accounts.

We feel that the purpose of a read-only role is to give a level of privilege that grants a no greater level of access than reading the source code would. For that reason, we have chosen to explicitly prevent the `ReadOnly` role from reading secret values from both AWS SecretsManager and AWS Simple Systems Manager Parameter Store. We have also prevented it from reading objects within Amazon S3.

We will ensure that engineers can assume the role in the same way as our other roles; either with GDS CLI or using a predictable name in the console.

### Consequences

As a consequence of the decisions we've made, we will have an additional role to maintain over time. We believe this is a minimal burden, and by choosing to prevent its access to secrets and objects in S3 we feel we have further mitigated any risks it poses.

## 16. Use IAM roles for external services and applications

Date: 2026-06-20

### Status

Accepted

### Context

<!-- vale RedHat.PassiveVoice = NO --> Many services currently use IAM access keys, which are assigned to IAM users and inherit all permissions granted to those users. If these keys are compromised through leakage or reuse by unauthorised actors, they can pose a significant security risk. Long-lived keys increase this risk, and regular rotation is encouraged to mitigate it. <!-- Passive voice makes sense in this context --> <!-- vale RedHat.PassiveVoice = YES -->

Many third-party services now support the use of IAM roles. Using IAM roles allows a trust relationship to be established so that external AWS accounts or infrastructure can assume the role and its associated permissions.

For internal applications (hosted within our AWS accounts), AWS access keys are sometimes used to access resources. Where possible, these applications (or their Kubernetes pods) should use Kubernetes `Pod` identities or assume IAM roles directly, rather than relying on access keys.

### Decision

We have decided to retire (delete) IAM users and their associated access keys, replacing them with suitable IAM roles. This change will occur when:

- We identify a long-lived access key that is a candidate for rotation.
- The service using the access key supports assuming IAM roles.
- The application using the access key can adopt a `Pod` Identity.

This change reduces attack vectors, strengthens our security posture, and aligns with the Principle of Least Privilege.

One recent example of this change is our work around [reconfiguring Fastly to use IAM Roles instead of Access Keys](https://github.com/alphagov/govuk-infrastructure/issues/2226).

### Consequences

As a result of this decision, we will have fewer access keys to manage and rotate. However, each time we identify a candidate for migration to roles or pod identities, we will need to do additional work will to create or manage the necessary IAM roles and permission policies.

## 17. Retire use of GitHub topics for configuration management

Date: 2026-08-06

### Status

Accepted

### Context

Historically, GOV.UK has used GitHub topic tags to select and configure repositories for things such as enforcing standard configurations or granting variables (including secrets) to sets of repositories.

An ITHC highlighted this as an issue for several reasons, including:

- Use of topics is not access-controlled or restricted. Anyone who has access to a repository can assign them, making it possible to accidentally (or intentionally) bring an unexpected or undesired repository into configuration scope.
- GitHub incidents have resulted in the GitHub search API returning unexpected (or no) results, negatively impacting Terraform runs and resulting in the undesired removal of Elastic Container Registry repositories or CodeCommit mirrors.

### Decision

We have decided to stop using GitHub topics as selectors or identifiers for our automation scripts, including Terraform. As a consequence, we must now configure our GitHub repositories using configuration files or in code explicitly, rather than implicitly through remotely-managed tags or labels.

We have documented the changes spurred from this decision have in the [GOV.UK Developer Docs](https://github.com/alphagov/govuk-developer-docs/pull/5187). They predominantly affect the [GitHub Terraform deployment](https://github.com/alphagov/govuk-infrastructure/tree/main/terraform/deployments/github).

Repository owners can still set topics for the purpose of making repositories easier to filter, search or organise. However, owners must no longer use them as selectors for automations or scripts.

### Consequences

As a result of this decision:

- We will need to remember to update any Repository configuration changes in code.
- Topics will no longer be able to grant Deployment Secrets to Repositories without oversight.
- Issues affecting the GitHub Search API will no longer risk breaking our Terraform in a way that is unsafe.

## 18. Use Concourse CI

<!-- Title contains proper nouns --> <!-- vale RedHat.Headings = YES -->

Date: 2025-08-12

### Status

Accepted

### Context

We have a continuous integration and continuous delivery (CI/CD) system composed of GitHub Actions workflows, ArgoCD deployments, and Argo Workflow runs. When a pull request gets merged into `main` in an application's source repository, a GitHub Actions workflow runs. The workflow builds a container image and instructs ArgoCD in the staging Kubernetes cluster to deploy it. On success, the staging cluster triggers the same action in the production cluster.

<!-- vale RedHat.SimpleWords = NO --> ![A flowchart depicting the existing CI/CD process outlined in the previous paragraph](../../img/adr-0018-existing-cicd.png) <!-- Warning against using "previous", but it's legitimate here --> <!-- vale RedHat.SimpleWords = YES -->

An IT Health Check carried out in 2024 identified security flaws in the implementation of the deployment process. This, and a number of incidents directly caused by this process, and the team's ongoing issues with Argo Workflows has led us to want to re-engineer our CI/CD pipelines.

An additional, contributing factor for making the decision was [ADR 0014](./0014-replace-terraform-cloud.md), in which we decided we would move away from Terraform Cloud. To do so will require us to have a replacement for automatically applying Terraform code in different environments.

#### Research

We held a team design day to discuss our CI/CD pains and come up with next steps for addressing them. The major outcomes of that day were decisions to investigate two different tools: Kargo and Concourse.

##### Kargo

[Kargo](https://kargo.io/) bills itself as a "multi-stage GitOps continuous promotion" tool. In short, it can take an artifact, deploy it in one place, validate it, and promote it to the next place and so on, in an automated fashion. That behaviour matched precisely what our existing workflow does across clusters, so we decided to try to replicate what we have using Kargo.

We planned to build a workflow that ran on a mock production Kubernetes cluster and orchestrated deployments to both a mock staging cluster and itself. Kargo is able to do it, but it relies on a feature called sharding. Sharding is available in the free open source version of Kargo, but its maintainers have said publicly that they [intend not to document it fully](https://github.com/akuity/kargo/issues/2447#issuecomment-3009092623), favouring driving users [toward their commercial offering](https://github.com/akuity/kargo/issues/4633#issuecomment-3176727119).

We did not want to rely on undocumented features, so we opted to prototype a workaround for the problem with Argo Rollouts to see how it would look and feel. The workaround worked, but it effectively disabled the deployment validation function of Kargo, and for that reason we decided it was not a good choice.

<!-- vale RedHat.SentenceLength = NO --> We ultimately decided that Kargo was not a good fit for what we wanted to do because the features we needed to make it work were intentionally left undocumented by the maintainers to encourage commercial adoption, and the workarounds were no good. <!-- It's a long sentence, but it's not too long --> <!-- vale RedHat.SentenceLength = YES -->

##### Concourse

[Concourse](https://concourse-ci.org/) is a "continuous thing-doer". It is generally un-opinionated, and functions as a flexible task runner based on Open Container Initiative (OCI) container images with YAML configuration of pipelines. It is not explicitly for deploying applications, but it is flexible enough for users to configure it for that purpose with ease.

We decided to experiment with Concourse by replicating our existing workflow, just as we did with Kargo, so that we could experience how it felt to use and deploy.

We deployed mock production and staging Concourse instances, along with mock production and staging Kubernetes clusters. We then built out a parameterised pipeline that we triggered with a Git commit, and subsequently built, deployed, validated, and promoted a container image.

We did not find any show-stopping problems in using Concourse. We experienced some friction and a learning curve, but nothing we felt was insurmountable or constituted a bad experience.

Our final recommendation was that we should take the next steps in replacing our CI/CD system with Concourse.

### Decision

After playing back both investigations into Kargo and Concourse, the team decided to pursue Concourse as its CI/CD tool of choice.

In our research we deployed it on virtual machines in EC2, because we borrowed Terraform code from another team to speed our prototyping time. We discussed the implications of running EC2 instances versus running Concourse in the Kubernetes clusters, and we decided that we should stay away from running virtual machines. It adds additional infrastructure for us to support long term, which is different from everything else we support.

By adopting Concourse over a combination of GitHub Actions, ArgoCD, and Argo Workflows we feel we are making a tradeoff. We are trading a deployment system we have intimate knowledge of, but is complex and fragile, for a new tool that we believe can simplify and make the process more reliable

### Consequences

As a consequence of our decision to adopt Concourse, we have two unanswered questions:

- 1. In what architecture will we deploy it?
- 2. How will we write the pipelines?

Both of these questions will, when answered, receive ADRs of their own.

Another consequence of our choice is its impact on the developer teams who rely upon us, and our CI/CD systems. Once we know more about what we will be changing and how, we will need to write new documentation and engage with teams to teach them about the changes we're making.

We expect that we will not switch over to Concourse all in one go. This means that we will double our maintenance costs for a period of time, and that we will increase our support burden while we have teams on both systems. These costs will reduce when we have finished moving to Concourse.

## 19. Restructure CI/CD

Date: 2025-10-16

### Status

Accepted

### Context

This ADR aims to document the Platform Engineering team's goal state for the process applications(and the platform itself) go through to get from source code to a production system. Most of the thinking and debate over this has happened between June 2025 and October 2025, in various documents, conversations, and team meetings. The final structure we are documenting here is the product of team design sessions on 15th October 2025.

#### The problem

In June 2024 we had an IT Health Check conducted that flagged some critical vulnerabilities in the fundamental architecture of our CI/CD processes. In April 2025, we also carried out some user research with the application teams, our senior management team, and ourselves to learn about the pain points involved with our current setup.

The nature of the vulnerabilities and the specific things we learned from the research are out of scope here. However, between those two data points, our own generalised dissatisfaction, and our decision to [replace Terraform Cloud](./0014-replace-terraform-cloud.md) we felt that a total rework would be the best option.

#### Technology choice

In the lead up to making the decisions documented here, we went through a small number of investigations to select the technologies we wanted to use. We did this knowing from experience that we would be able to solve the problems we would need to solve using whatever technologies we chose.

The researched culminated in us [deciding to use Concourse CI](./0018-use-concourse-ci.md) as our CI/CD tool of choice.

At this time of writing, there is ongoing research into the tool we should select for YAML generation. A subsequent ADR will cover that choice.

### Inputs into the decision-making process

In the run-up to the team design session on 15th October 2025, we put together a number of documents whose contents would feed into how we evaluated our options.

Firstly we wrote down what we felt to be our [core principles of secure CI/CD](https://docs.google.com/document/d/1P4ZNrY2N4sq_XtVmPZLFjiYQ6L-dSeNzrr7sONPK6zo/edit?usp=sharing). These principles describe the properties that any solution we come up with must have. We used them to help us evaluate the options in front of us, and we intend to use them in the future to evaluate changes and additions.

Second we wrote down what we felt should be [the guiding ideas for what we want the GOV.UK platform to become](https://docs.google.com/document/d/1PiJmHrmFWI98PydSY2Jq4UWHh3PuwZITkmHnQc-UzjY/edit?tab=t.0#heading=h.jahzhj4gax23). Expressing these ideas in writing and reviewing them together helped us all get on the same page about what it should be to use our platform at a high level. Consensus on that will in turn guide the decisions we make.

<!-- vale RedHat.PassiveVoice = NO --> The final document we produced as input showed [the possible ways we could deploy Concourse](https://docs.google.com/document/d/1odUWlmmgVXlb5PlveA7j_jAbwlgsCb8zyKEIP472XvI/edit?tab=t.0). We used this to focus our discussions, and the options it presented are summarised for posterity in the next section. <!-- "are summarised" is a valid use of the passive voice in this context --> <!-- vale RedHat.PassiveVoice = YES -->

### Options

#### Option 1: Concourse on EC2

Under option 1 we would run Concourse on EC2 instances, either in each environment or as a central management cluster. This is how the GOV.UK Pay team runs Concourse, and we would be able to crib a lot of code from them to get started.

We immediately dismissed this option because EC2 is not a service we use directly elsewhere. We would have to do a lot of work to build out and maintain the Concourse infrastructure in comparison to running it in Kubernetes.

#### Option 2: Concourse on Kubernetes in a management cluster

Under option 2 we would create a new AWS account, and in it a new Kubernetes cluster. That cluster would run the Concourse web node and a number of worker nodes.

To perform deployments, the workers would require privilege enough to reach into other environments.

Going down this route would give us a single place to run deployments from, which would make it easy to see the state of any deployment across all environments. It would also give us a convenient place to run the types of jobs that aren't related to one environment, such as configuring GitHub access.

It would also present all the risks associated with crossing the already established security boundaries around the existing environments, and its level of privilege would make it an obvious target for attackers.

From a reliability perspective, a management cluster in control of deployments to all environments represents a large single point of failure.

#### Option 3: Concourse in each application cluster

Under option 3 we would run the Concourse web node and its workers directly on the Kubernetes cluster in each environment. It would be responsible for, and have permission to, deploy to the environment in which it runs.

Choosing option 3 would give us good separation between the environments, but would present additional maintenance burden. It also does not address the needs of development teams to see the state of their deployments across all environments in a single place.

#### Option 4: Separate infrastructure and application Concourses per environment

Option 4 is very similar to option 3, but we would have a separate Concourse deployments for infrastructure changes and application changes. This would further separate the levels of privilege needed, but would contribute further to the maintenance burden.

#### Option 5: One Concourse on one cluster with all the environments

<!-- vale RedHat.PassiveVoice = NO --> Option 5 was brought up and discussed briefly on the team day on 15th October 2025. The proposal would be to begin deploying teams' staging and integration applications into the production cluster, with suitable isolation and security controls. <!-- "was brought up" is a valid use of passive voice here --> <!-- vale RedHat.PassiveVoice = YES -->

The platform engineering team would maintain integration and staging clusters for the purposes of developing and testing changes to the platform, but the applications running on them would be synthetic ones.

The effect of this change would be to turn the production cluster into _the platform_. This is similar to the way that users of Heroku deploy all of their development, staging, and production code into Heroku's production system.

### Decision

The decision we have landed on is a blend between options 2 and 3. We will have a Concourse deployment in each environment, with a central Concourse deployment in a "tools" account or similar. The central Concourse will not have permission to reach into other accounts.

<!-- vale PlatformEngineering.AsConjunction = NO --> The Concourse deployment in each environment will, as in option 3, be responsible for deployments to the environment that it lives in. <!-- "as in" is a similie, not a conjuction --> <!-- vale PlatformEngineering.AsConjunction = YES -->

The central "tools" Concourse deployment however has a different purpose.

#### The role of a central Concourse

During the team's discussions, we noted that under option 3 we would need to rebuild any artifacts at the beginning of each run. Conceptually this should be OK because the artifacts we build are reproducible, and running the build twice should always result in the same output. However, we noted that we have seen that this is not the case in practice on a number of occasions, across a number of applications in recent memory.

We believe the cause was Ruby On Rails' asset pre-compilation being flaky. We have observed that in most cases the built container image correctly includes assets, but in a few unpredictable cases the process that generates them fails, but the build continues. Therefore, increasing the number of builds taking place during a deployment will increase the number of instances of bad artifact builds.

As a team we briefly considered bringing the failures up with the relevant team and working with them to fix it. However, we realised that every team that uses Ruby On Rails can experience the problem, because the issue is with Rails' asset pre-compilation.

We instead settled on the fact that we must build the artifacts a single time at the beginning of a deployment, verify them, and reuse them across environments. This is the same behaviour as in our existing system, where we build the artifacts in GitHub Actions.

We decided we did not want to continue with GitHub Actions building our artifacts because we find it to be too slow and unreliable for that purpose. We instead decided to introduce a central Concourse deployment, on which the artifact builds could take place.

Introducing a central Concourse deployment for this purpose has a couple of useful benefits.

- 1. We can have dedicated machines for fast artifact builds
- 2. It provides us a convenient place to run the kinds of jobs that do not relate to a specific environment.

#### Versioning infrastructure manifests

A secondary decision that we made during the team discussions on October 15th 2025 was to begin versioning the manifest files for application infrastructure, just as we do for application source code.

Currently, we use a Git repository called `govuk-helm-charts`. It holds our central `generic-govuk-app` Helm chart code, and the values for all the applications that make use of it. When a new version of an application container needs deploying, the process updates the repository to set the value in a file. ArgoCD subsequently detects the change, renders the manifests, and synchronises the cluster with them. As a result of this, the repository has 190,000+ commits at the time of writing.

In each environment, our pipelines will render manifest files in each application repository by using whatever technology we select for YAML generation. We will store the rendered manifest files in a Git repository, which ArgoCD will synchronise from.

#### Path to production

The decisions we have made about how we architect Concourse have a direct impact on how application code reaches production. We expect that the process now looks like

- 1. Merge to `main`
- 2. Build container, tag with Git SHA, push to registry
- 3. Detect container tag in pipeline
- 4. Fetch source from Git at same SHA as container
- 5. Render manifests
- 6. Store in Git
- 7. Trigger ArgoCD synchronisation
- 8. Wait for deploy success/fail
- 9. If success, re-tag container image to indicate successful deployment
- 10. Go to 3 if there is a higher environment

Code: flowchart TD ⏎ subgraph Git ⏎ merge["Merge to main"] ⏎ end ⏎ subgraph Central Concourse ⏎ central_build["Build container"] ⏎ central_push["Push to registry"] ⏎ merge --> central_build ⏎ central_build --> central_push ⏎ end ⏎ subgraph Environment ⏎ central_push --> ⏎ env_detect["Detect container tag"] --> ⏎ env_fetch["Fetch source from Git with same SHA"] --> ⏎ env_render["Render manifests"] --> ⏎ env_store["Store in Git"] --> ⏎ env_wait["Trigger ArgoCD synchronisation"] --> ⏎ env_success{"Deployment success?"} ⏎ env_retag_image{"Retag container image"} ⏎ env_higher_env{"Higher environment?"} ⏎ env_success -- No --> env_fail(("Fail")) ⏎ env_success -- Yes --> env_retag_image ⏎ env_retag_image --> env_higher_env ⏎ env_higher_env -- No --> Stop(("Stop")) ⏎ env_higher_env -- Yes --> env_detect ⏎ end

### Consequences

#### Time and energy

<!-- vale RedHat.TermsSuggestions = NO --> To implement the decisions we have made we expect will require a large investment of time and energy, over the course of at least a year. During that time we expect to have different applications reaching production in different ways, and there to be some amount of confusion over which application is using which process. We accept this as a cost of doing the rework. <!-- "which ... is using which ..." is an OK use of "which" --> <!-- vale RedHat.TermsSuggestions = YES -->

Because of the long timeline, there is also a risk we will need to shelve the work part way through in favour of a more urgent piece of work.

#### Technical debt

Whilst we rework our CI/CD infrastructure, we know that we will have to make compromises and have messy code in different parts of the system. This will inevitably pile up as technical debt. We will do our best to prevent this and pay down debt as we go, but there is very likely to be some left over when we finish.

#### Cost

There will be a minor rise in the cost of running each environment, and an additional cost for the new "tools" account. In each environment we expect to run at least one new node in Kubernetes for Concourse, plus its database. In the new account the costs will include a new Elastic Kubernetes Service cluster control plane on top of the nodes and database.

#### Better security posture

We believe that the choices we have made regarding CI/CD architecture addresses the most critical of the findings of the 2024 ITHC. Addressing these findings leaves us with a much better security posture, and good base on which to layer additional security controls at a later date.

## 20. Use Crossplane for abstraction

Date: 2025-10-20

### Status

Accepted

### Context

Applications deployed on Kubernetes need a number of different resources to function: pods, replica sets, deployments, services, ingresses and so on. Knowing what resources you need, their configuration, and how their interrelations requires a good amount of Kubernetes knowledge, and knowledge of the rest of your infrastructure. This knowledge is readily available within the Platform Engineering team, but less so among the application teams we serve.

To address this, and to try to standardise and simplify the way teams were deploying applications, we built a generic Helm chart. We intended the chart to support every team, no matter what they needed. As a result, over time it grew to include a lot of components: database migrations, Redis, cron jobs, autoscaling, service accounts and more. For us, as a Platform Engineering team, this had led to a code base that:

- has lots of Golang templates embedded in YAML,
- has lots of importing and variable values derived from other variables,
- is hard to navigate,
- is hard to reason about,
- is hard to change,
- and is easy to get wrong.

Given these failings, we have wanted to improve the way that teams describe the Kubernetes resources needed for their applications in one way or another.

A number of team members had been aware of [Crossplane](https://www.crossplane.io/), a "Cloud-Native Framework for Platform Engineering", for some time. In a firebreak in September 2025, we decided to experiment with it. We had good experiences with it, and at a post-firebreak show and tell the team was enthusiastic about the possibilities presented by Crossplane's capabilities.

In our team design day on October 15th 2025 we made the decision to use Crossplane.

#### Crossplane features

Users can [extend the Kubernetes API](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/) using custom resources. Crossplane extends the API with a `CompositeResource` resource type, a resource type that "represents a set of Kubernetes resources as a single Kubernetes object". It also creates a `CompositeResourceDefinition` resource type that describes the schema of a custom API.

<!-- vale RedHat.TermsWarnings = NO --> A third feature of Crossplane is compositions. Compositions are like templates for turning an object described by a `CompositeResourceDefinition` into a `CompositeResource` and the other Kubernetes resources it represents. <!-- Warns of using "like" instead of "such as". But here it's a simile --> <!-- vale RedHat.TermsWarnings = YES -->

Another feature of Crossplane we plan to use is its ability to create cloud resources when a custom type gets submitted to the API. For example, we can define a `PostgresDatabase` type by using a `CompositeResourceDefintiion`, and we can create a new database instance when a user submits it.

### Decision

<!-- vale RedHat.TermsSuggestions = NO --> We have decided that we want to use Crossplane to create a Kubernetes-flavoured API for our users. The API will abstract the types of resources our users need to create at a higher level than offered by the standard Kubernetes API. <!-- "higher" in "higher level" is a different context than the check is assuming --> <!-- vale RedHat.TermsSuggestions = YES -->

The finer details of what Crossplane is and how it works are out of scope for this ADR. We give light touch explanations here to contextualise the decisions we have made.

#### Creating an API

We plan to create an API with types that represent the high-level concepts our users want to deploy: apps, backing services, routes and so on. The actual types we will need to create are not yet decided on; the aforementioned types are simply illustrative.

#### Backing services

We plan to use this feature to create a catalogue of backing services our users can get access to through Kubernetes. This will eventually replace creating application backing services in Terraform. The backing services we will offer are not yet decided.

#### Changing where the code lives

Another decision we made as part our decision to use Crossplane is to change where teams' application infrastructure source code lives. Today, each application has a set of YAML files providing values for the generic Helm chart in a single Git repository.

Teams make changes to their application infrastructure by modifying the YAML files in the repository. They can work with us to modify the Helm chart if they need something new, or that they cannot change with a variable.

When performing a deployment, an automated process updates the relevant YAML files with the new container image tags.

We plan to move from a model where every application's infrastructure code lives in the same repository, to one where each application repository has its own infrastructure code. We do not yet know what that code will look like; we expect we will make the decision in an upcoming ADR about our choice of YAML generation tool.

<!-- vale RedHat.PassiveVoice = NO --> The way in which this affects the deployment process is documented in [ADR019](./0019-restructure-cicd.md). <!-- vale RedHat.PassiveVoice = YES -->

#### Stages of implementation

Our implementation of Crossplane and a new API abstraction will likely have three phases. We will describe here what we expect the three phases to look like, but offer no timelines.

##### 1. Ideation and alpha implementation

We will begin by working out what concepts we want to include in the abstraction, and how we should implement them. This will form an alpha version of the API. We will build out enough of it to be able to approach a team about migrating their application infrastructure to using it. We know that we will learn much more about what the API should look like and how we should implement it by making use of it in production.

##### 2. Migration of all applications

After we have worked with one team to begin using the new API, we will systematically work through every application from every team to migrate them to the new API. This will take a long time.

##### 3. Migration of backing services

In the last two stages, we will have focussed on the way in which teams' applications get deployed. In the third and final stage, we will create a service catalog in the Kubernetes API and migrate all existing backing services to be represented and managed by that API.

### Consequences

#### Time and energy

<!-- vale RedHat.TermsSuggestions = NO --> To implement the decisions we have made we expect will require a large investment of time and energy, over the course of at least a year. During that time we expect to have different applications with different methods of describing their infrastructure, and there to be some amount of confusion over which application is using which method. We accept this as a cost of doing the rework. <!-- "which ... is using which ..." is an OK use of "which" --> <!-- vale RedHat.TermsSuggestions = YES -->

Because of the long timeline, there is also a risk we will need to shelve the work part way through in favour of a more urgent piece of work.

#### Technical debt

Whilst we rework our CI/CD infrastructure, we know that we will have to make compromises and have messy code in different parts of the system. This will inevitably pile up as technical debt. We will do our best to prevent this and pay down debt as we go, but there is very likely to be some left over when we finish.

#### Increased need for quality documentation

We will need to produce more good quality documentation for the API we are producing. To date we have been able to rely on the Kubernetes documentation, but for our own API we will be the sole authority.

#### Increased test coverage required

The new API, compositions, cloud resources and so on will require us to have a better test suite for the platform itself. We will have to expand our end-to-end test, smoke test, and integration test suites.

## 21. Give Fastly CNAME records a TTL of 300

Date: 2026-10-27

### Status

Accepted

### Context

GOV.UK uses Fastly as its Content Delivery Network (CDN). Public users don't access GOV.UK servers directly but connect through Fastly. `www.gov.uk` is a CNAME record pointing to `www-cdn.production.govuk.service.govuk`, which is itself a CNAME record pointing to Fastly.

`assets.publishing.service.gov.uk` is also a CNAME record pointing to Fastly.

In the event that an incident with Fastly occurs we fail over to our backup CDN by pointing both CNAME records to AWS CloudFront.

Currently, we have set the TTLs for these CNAME records to 1 hour. This means that in the event of an incident with Fastly it will take up to an hour before we can restore service.

### Decision

We have decided to give Fastly CNAME records for `assets.publishing.service.gov.uk` and `www-cdn.production.govuk.service.gov.uk` a TTL of 300.

### Consequences

As a result of this decision, in the event of an incident with Fastly we will be able to fail over to AWS CloudFront and restore service to users quickly.

## 22. Use Pkl for configuration

Date: 2025-11-06

### Status

Accepted

### Context

In ADRs [0018](./0018-use-concourse-ci.md), [0019](./0019-restructure-cicd.md), and [0020](0020-use-crossplane-for-abstraction.md) we have made the decisions to use Concourse CI, restructure how we do CI/CD, and to begin using Crossplane.

Each of these tools and choices will require us to configure different things, such as Concourse and its pipelines, and Crossplane's composite resources. The native configuration language for each of them is YAML.

As a team, we already maintain a lot of YAML code across things such as [our Helm charts](https://github.com/alphagov/govuk-helm-charts), our [user access management](https://github.com/alphagov/govuk-user-reviewer), and [our DNS](https://github.com/alphagov/govuk-dns-tf). We know from experience the pain involved with maintaining large amounts of YAML. It's especially when it is also maintained by people outside the team, or when it is being fed into another process that asserts a number of unwritten rules about it.

Before we embarked on adding more YAML for us to maintain, we wanted to explore what options existed for generating YAML from another language or tool. The positive attributes of something in this role would include

- strong typing,
- an ability to model schemas and constraints,
- validation,
- good IDE support,
- and being able to output both YAML and JSON

#### Research method

Our research method for finding the right thing for us had three stage: a long list, a short list, and a team discussion.

At the long list stage, we went looking across the internet for tools and languages that were doing the kinds of job that we were looking to fill. We drew up some rough criteria to compare them against: how they get installed; the quality of their standard libraries; how well supported they were by common IDEs. We eventually selected three to go on the short list.

At the short list stage we exercised the options in two ways

- 1. Writing code to replace our existing YAML for user access management; this is a data driven application with lots of repeated blocks with minimal changes (for example, just a name and email address changing)
- 2. Writing a Concourse pipeline in as concise and maintainable way as possible

At the final stage we presented the findings of the short list back to the team, and discussed the various trade-offs and concerns.

#### What did we evaluate

At the long list stage we evaluated

- [KCL](https://www.kcl-lang.io/)
- [Pkl](https://pkl-lang.org/)
- [Jsonnet](https://jsonnet.org/)
- [Dhall](https://dhall-lang.org/)
- [Cue](https://cuelang.org/)`
- Ruby
- Go
- JavaScript/TypeScript
- Python

From those, we short-listed

- KCL
- Pkl
- Go

##### Reasons for dropping at the long list stage

At the long list stage we dropped two thirds of the things we investigated. We explain here, in brief, why we dropped each one.

###### Jsonnet and Dhall

Jsonnet and Dhall are both viable options in this space. However, they did not perform as well in our assessment. Jsonnet's package libraries rely on third-party bundling of code into independent framework-like packages, and Dhall lacked support for IntelliJ IDEs.

###### Cue

We chose not to continue with Cue because it lacks any official IDE support, and its package library ecosystem is slim to non-existent.

<!-- vale RedHat.Headings = NO -->

###### JavaScript and Python

<!-- Title contains proper nouns --> <!-- vale RedHat.Headings = YES -->

JavaScript and Python are both general purpose languages that would be up to the task, and have strong IDE support. We chose not to proceed with them because of their large installation footprint and constantly moving package ecosystem. The type of code we're writing usually end up written one time, and modified a small number of times, but otherwise being static for years. Having a package ecosystem that requires constant bumps would be burdensome.

###### Ruby

Ruby has similar problems to JavaScript and Python. We opted not to proceed with it because there are no pre-existing, relevant packages in its ecosystem. It would otherwise be a contender, because Ruby is a well-used language in GOV.UK.

##### Reasons for not selecting at the short list

We ultimately chose not to use Go or KCL; the rationale for choosing Pkl is in the decision section.

###### Why not KCL

KCL and Pkl are similar in their design goals, purpose, and function. However, we found that KCL lacked some of the features of Pkl, had some unfortunate shortcomings, and overall wasn't as mature or battle-tested as Pkl.

The first flaw we found, in comparison to Pkl, was a lack of validations and constraints on types. For example, in Pkl we can write this:

Code: typealias Identifer = String(StartsWith("_"))

Which defines a type `Identifier`: a string that must begin with an underscore. Every instance and use of that type will get constrained to that rule, and that rule will get checked on every instance.

KCL has no such functionality. The closest replica is performing the validation of the constraint on every string that you know to be an identifier. This is repetitive and error-prone.

The second flaw we found was in KCL's polymorphism. KCL allows a user to define schemas (essentially classes), and for one schema to extend another. However, unlike inheritance and polymorphism in most object oriented languages, KCL does not allow for a child type to change or further constrain the type of an attribute.

This flaw would be particularly bothersome when dealing with Concourse pipelines, where a number of things are generically defined as a map of `string` to `any`. To make good use of a strongly typed configuration language, it would be very useful to be able to extend the generic `Resource` type. For example, to create a more concrete `GitResource` type with attributes for the keys required in the underlying map.

With respect to the maturity of the language, we found KCL lacked in two areas:

- 1. **Syntax highlighting**

There is no syntax highlighting available in GitHub at the time of writing, which would make reading and reviewing the code harder than it ought to be. There is an open issue for adding support, but it seems to be a long way from happening.

- 2. **Editor support**

A language server protocol implementation exists for KCL, but in Visual Studio Code and Vim we found it to be only just usable, and would crash when encountering cyclic dependencies. We did not try it in JetBrains' IDEs.

By comparison, Pkl's editor support is strong and mature in all IDEs.

<!-- vale RedHat.Headings = NO -->

###### Why not Go

<!-- Title contains proper nouns --> <!-- vale RedHat.Headings = YES -->

Go is a significantly different prospect than KCL or Pkl. Given that, we effectively compared the flexibility of Go with the productivity of KCL and Pkl.

<!-- vale RedHat.PassiveVoice = NO --> In favour of Go we found that much of the team was already familiar with the language, and many of the open source projects we use (especially Concourse) are written in Go. As a result we are able to make direct use of the exact data structures those projects use for configuration. <!-- "are written". Valid passive voice --> <!-- vale RedHat.PassiveVoice = YES -->

We also found that the flexibility of Go as a general purpose language granted us the freedom to implement things to exactly meet our needs.

The flip side of this flexibility is the need to do just that: implement everything. Where KCL and Pkl have built-in, lightweight data modelling and serialisation, Go does not. One achieves that by creating new types and using additional libraries. Atop this, Pkl, and to a lesser extent KCL, have good systems for constraining and validating inputs as part of the language itself. Whereas in Go developers must implement it in addition to the modeling and serialisation.

Data modeling, serialisation, and validation of the types of configuration code we want to generate are not difficult problems. The challenge lays in the volume of code needed, both in a single usage and across the entire estate, and the potential for variability of quality in that code. Pkl and KCL, being domain specific languages, have a uniform approach to all of these problems, thereby reducing the variability between usages.

Go also imposes an additional, lifelong dependency maintenance burden for every single usage, both of the language version and of all dependencies taken by the code. By comparison, KCL and Pkl have very minimal dependency footprints - a single binary - and the same language version can be in use globally across all usages.

### Decision

After the research and discussion outlined in the Context section, we have decided to use Pkl for configuration code going forwards.

We have chosen Pkl because, of the options we short-listed, it was the most mature, well-supported, and feature rich option. It has strong support in IDEs and on GitHub, as in Go, but does not burden us with ongoing dependency maintenance. It is strongly typed, and has native input constraints and validations; and it is a small enough language for maintainers to fully understand and write code of a consistent approach and quality.

We acknowledge that in choosing Pkl we are introducing another language into our toolkit, with everything that entails. We feel that this is a worthwhile tradeoff against the effort required to get a result of variable quality in Go. Pkl's scope is small and well-defined, and it does not lend itself to use in places to which it is not suited.

### Consequences

As a consequence of choosing a new language for configuration, we will be drawing a line, either side of which will be the old and new way of doing things. At first this will mean that all of our configuration code is on the old side of the line, but over time that percentage will get smaller.

We acknowledge that there are probably some configuration we will never rewrite. We will not consider that to be technical debt, for as long as it is actively maintained and in use in some capacity.

We think that Terraform configuration code is out of scope for conversion to Pkl, because HCL is the accepted and supported language.

We intend Pkl code to replace as much of our YAML code as possible, including the YAML maintained by our non-engineer colleagues. The team will commit to learning Pkl itself, writing documentation for using our Pkl codes bases, and giving training where necessary.

## 23. Use OPA Gatekeeper

Date: 2026-07-07

### Status

Accepted

### Context

We have assessed and made this decision in the context of a piece of work to implement a job request and approvals system in Kubernetes. However we believe the needs and benefits will be more generally applicable to the platform down the line.

We can state the specific user need we wanted to meet in the discovery as:

> **As a** security conscious engineer building a job request and approval system <br /> > **I want** to prevent a user from requesting and approving their own jobs <br /> > **So that** a malicious user cannot bypass a second human reviewing the content of a job

We can meet our need by making assertions about objects submitted to the Kubernetes API, and rejecting them in the event they don't meet the criteria.

More generally, the problem we are looking to solve is applying policies to objects beyond those that enforced by Kubernetes itself.

The single other requirement we set ourselves for choosing a tool was the ability to perform automated testing of the policies in isolation of a full Kubernetes cluster. We want this so that we can treat policy code as we would application code, with full sets of tests we can trust when making changes in the future.

To that end, we chose to test two tools:

- [Kyverno](https://kyverno.io/)
- [Open Policy Agent (OPA) Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/)

<!-- vale RedHat.PassiveVoice = NO --> <!-- "are implemented" is valid in this context -->

Both tools are implementations of Kubernetes' [admissions webhooks](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#what-are-admission-webhooks), but differ in how they are implemented: Kyverno uses a YAML format, or [CEL](https://cel.dev/) expressions, to express its policies, whilst OPA Gatekeeper uses [Rego](https://www.openpolicyagent.org/docs/policy-language).

<!-- vale RedHat.PassiveVoice = YES -->

Both tools were capable of meeting the needs we had.

### Decision

We have chosen to adopt OPA Gatekeeper for applying policy to Kubernetes objects because it is a mature CNCF graduated project with good adoption among other Kubernetes users.

We also view its dedicated Rego language as a positive. It is testable, not overly complicated or hard to learn, and adopting it meshes well with our [decision to adopt Pkl](./0022-use-pkl-for-configuration.md) as our preferred configuration language over YAML.

We also have a number people in the team at the time we've made the decision with strong, positive, open source experience of running and working with OPA Gatekeeper. We will be able to accelerate our adoption and maturation by leaning on their experience and past work.

Finally, choosing OPA Gatekeeper dovetails nicely with our [decision to adopt Concourse](./0018-use-concourse-ci.md), because it also makes use of [OPA to implement custom policies](https://concourse-ci.org/docs/operation/opa-integration/).

### Consequences

We will deploy OPA Gatekeeper to all of our Kubernetes clusters. Initially we will deploy it in audit mode, where it will report what the outcome of applying a policy would be, without applying it. We will slowly introduce new rules, taking good practices rules from trusted sources, until we are confident that enforcing the policies would not have negative effects.

We also commit to ensuring that each of our policies have suitable test suites.

## 24. Use of admission policy

Date: 2026-08-07

### Status

Accepted

### Context

Starting with Kubernetes version 1.36 Validating and Mutating Admission Policies are enabled by default. Admission Policies are a declarative, in process alternative to admission webhooks. They are appealing because the are more performant and simpler. Policies are quite configurable and they are written with YAML and Common Expression Language (CEL).

The strengths of Admission Policies are:

- native in-process
- reduces admission request latency
- improves reliability and availability
- avoids the operational burden of webhooks
- can mutate resources with access to `userInfo` field in the admission review object

### Decision

Keep using Open Policy Agent (OPA) and Rego.

Pick Gatekeeper and Admission Webhooks over CEL and Admission Policy where possible.

OPA proves particularly useful for the team, as we [expect to utilise the engine](https://concourse-ci.org/docs/operation/opa-integration/) with our upcoming [concourse work](./0018-use-concourse-ci.md).

### Consequences

Our choice to prioritise Gatekeeper, Rego and the OPA engine means that engineers will have less languages and approaches that they need to hold in their head.

We will stay flexible and still have the option to use Admission Policies when we need, otherwise we'll continue leveraging the efficiency gains of already well known technologies.

There are a couple of scenarios where Gatekeeper cannot meet our needs. They are:

- When we need to write a mutation that requires looking up data from the `userInfo` field in the `AdmissionReview` object
- When we need a performant admission

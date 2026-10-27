# Real-document sources

Held-out evaluation documents. Development set (used while building the harness): Backstage, GOV.UK, JSON Resume. Held-out set 1 (`fresh`, requests quote the text): MoJ, Common Paper, RenderCV. Held-out set 2 (`fresh2`, plain-language requests, never used for tuning): log4brains, GOV.UK Infrastructure, Bonterms, best-resume-ever. Source files are kept unmodified under `sources/` with their
licences; `convert.py` produces the corpus dialect (`*.md` here). Fetched 2026-10-16 at the pinned commits.

| Doc | Source | Commit | Licence | Notes |
|---|---|---|---|---|
| `backstage-adr.md` | [backstage/backstage](https://github.com/backstage/backstage) `docs/architecture-decisions/` (index + ADR001–ADR015; template excluded) | `a0a4a70c96ee194b6c27ecd9ffea1b21157562ab` | Apache-2.0 (`sources/backstage/LICENSE`) | © The Backstage Authors |
| `govuk-adr.md` | [alphagov/govuk-aws](https://github.com/alphagov/govuk-aws) `docs/architecture/decisions/` (0001–0039, 38 records) | `81ee9f6e91fd8692fbf751ecf980c671c13aa3c0` | MIT (`sources/govuk-aws/LICENCE`) | © Crown Copyright (Government Digital Service) |
| `cv-jsonresume.md` | [jsonresume/resume-schema](https://github.com/jsonresume/resume-schema) `sample.resume.json` | `b25e3f4bbafd349c2c5bbaa62602c03c228762db` | MIT (`sources/jsonresume/LICENSE.md`) | Fictional sample résumé |
| `moj-adr.md` (fresh) | [ministryofjustice/cloud-platform](https://github.com/ministryofjustice/cloud-platform) `architecture-decision-record/` (50 records) | `ff9b93bbe23f874d23c3ec14e5ec846a01bdac83` | MIT (`sources/moj-cloud-platform/LICENSE`) | © Crown Copyright (Ministry of Justice) |
| `commonpaper-csa.md` (fresh) | [CommonPaper/CSA](https://github.com/CommonPaper/CSA) `CSA.md` (Cloud Service Agreement standard terms) | `3efceb01e3c8bfb7b302a5f34975aa2b084026a3` | CC BY 4.0 (stated in `sources/commonpaper-csa/README.md`) | © Common Paper, Inc.; HTML spans stripped, clause numbers kept |
| `cv-rendercv.md` (fresh) | [rendercv/rendercv](https://github.com/rendercv/rendercv) `examples/John_Doe_ClassicTheme_CV.yaml` | `1d4b87bc427e4cf61c0ef49623c971b0e2224708` | MIT (`sources/rendercv/LICENSE`) | Fictional sample CV |
| `log4brains-adr.md` (fresh2) | [thomvaill/log4brains](https://github.com/thomvaill/log4brains) `docs/adr/` (MADR format) | `17e32021a8c5130386f17e921d4efa6da7709a66` | Apache-2.0 (`sources/log4brains/LICENSE`) | © Thomas Vaillant |
| `govuk-infra-adr.md` (fresh2) | [alphagov/govuk-infrastructure](https://github.com/alphagov/govuk-infrastructure) `docs/architecture/decisions/` (24 records; template excluded) | `3df5c3ec5f13a44135e0f89d394f42526be684aa` | MIT (`sources/govuk-infrastructure/LICENCE`) | © Crown Copyright (Government Digital Service) |
| `bonterms-cloud.md` (fresh2) | [Bonterms/Cloud-Terms](https://github.com/Bonterms/Cloud-Terms) `Cloud-Terms.md` (v1.0) | `df13f512c3bd923cc09cc2dae918812f876ea6e9` | CC BY 4.0 (stated in `sources/bonterms/README.md`) | © Bonterms |
| `cv-best-resume.md` (fresh2) | [salomonelli/best-resume-ever](https://github.com/salomonelli/best-resume-ever) `resume/data.yml` | `29e753cd842585b4a2e9dbbb5e1ef3a0f5e66767` | MIT (`sources/best-resume-ever/LICENSE`) | Fictional sample CV |

## Conversion (lossy, by design)

Headings, titles and wording are kept as in the source, including conventions the harness's rules do not
expect (e.g. "ADR013: [superseded] …", "1. Record architecture decisions", "Executive summary"). Constructs
the v1 parser can't represent are flattened: code blocks become one paragraph, table rows become bullets,
numbered and nested lists become flat bullets, and admonitions become a "Note (…)" line.

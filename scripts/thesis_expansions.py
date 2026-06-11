"""Additional paragraphs to expand thesis to ~50 pages."""

EXPANSIONS = {
    "1.1 Introduction": [
        "Recruitment is not merely an administrative function but a strategic enabler of organisational performance. When hiring processes fail to attract suitable candidates or produce defensible selection outcomes, downstream consequences include prolonged vacancies, increased training costs for ill-suited appointees, and erosion of employee morale. Public institutions face heightened scrutiny because employment decisions are often perceived as reflections of broader governance culture. Consequently, any technological intervention in recruitment must be evaluated not only for efficiency gains but also for its contribution to procedural justice and institutional reputation.",
        "The platform documented in this report addresses these multifaceted expectations through deliberate functional and non-functional design choices. For example, duplicate application prevention reduces administrative noise and ensures each candidate is evaluated once per vacancy. Structured interview criteria standardise assessment dimensions across candidates and across interviewers, while averaging logic treats each evaluator's judgement as equally significant unless policy dictates otherwise. Email notifications provide documentary evidence that candidates were informed of interview arrangements, supporting both courtesy and compliance objectives.",
        "From a pedagogical standpoint, the project illustrates how software engineering principles translate into sociotechnical outcomes affecting real users. Requirements are not abstract artefacts; they emerge from interviews with HR officers who describe genuine frustrations. Design decisions such as teal-and-orange branding are not cosmetic afterthoughts; they communicate institutional identity to applicants who may never visit a physical GMB office. Implementation trade-offs—such as JSON persistence for prototyping versus PostgreSQL for production—demonstrate how architects balance speed, cost, and scalability.",
        "Readers approaching this report from a management perspective may focus on Chapters One and Two for contextual and planning insights. Technical readers may emphasise Chapters Three through Five for requirements, architecture, and code-level behaviour. Regardless of entry point, the unifying theme is that technology should strengthen—not replace—the human judgement inherent in hiring, by furnishing decision-makers with timely, accurate, and complete information.",
    ],
    "1.2 Background of the Study": [
        "International experience with e-recruitment platforms suggests several success factors: intuitive applicant interfaces, reliable document upload, transparent status communication, and robust back-office dashboards. Failures in large-scale government hiring portals have often stemmed not from inadequate technology per se but from poor change management, insufficient HR training, and unrealistic timelines. This project consciously paired technical development with workflow mapping exercises to reduce adoption risk.",
        "The agricultural and commodity marketing sector in which the Grain Marketing Board operates introduces seasonal hiring peaks aligned with harvest cycles, storage operations, and policy implementation programmes. During these peaks, HR teams may receive hundreds of applications for a single advertised post. Without automated shortlisting support, reviewers experience cognitive overload and may inadvertently overlook qualified candidates buried deep in application queues.",
        "Digital literacy among applicants varies widely. The careers portal therefore avoids unnecessary complexity, presenting job cards with clear titles, departments, deadlines, and apply buttons. Where welcome videos or imagery are configured, they serve to humanise the institution and convey organisational values to first-time visitors. Accessibility considerations include readable font sizes, sufficient colour contrast on buttons, and form labels that screen readers can interpret.",
        "Research on applicant tracking systems also highlights legal and ethical obligations regarding data retention and privacy. Although detailed legal analysis lies beyond the scope of this technical report, the system architecture supports data minimisation by storing only application-related fields necessary for hiring decisions and restricting document downloads to authenticated HR routes.",
    ],
    "1.3 Vision": [
        "Realising the stated vision will require phased organisational change extending beyond software installation. HR policies may need revision to mandate use of the platform for all externally advertised vacancies. Training workshops should familiarise staff with screening dashboards, interview mark sheets, and interviewer link generation. Metrics such as time-to-shortlist and time-to-hire can be tracked once sufficient historical data accumulates in the system.",
    ],
    "1.4 Mission Statement": [
        "The mission statement emphasises service excellence toward both external applicants and internal users. Applicants benefit from confirmation messages and structured application flows. HR staff benefit from consolidated views that eliminate redundant data entry. Managers benefit from selection reports grounded in quantitative averages supplemented by qualitative notes captured during screening.",
    ],
    "1.5 Core Values": [
        "Operationalising values within software requires explicit rules. The platform encodes fairness by refusing to mark interviews as completed when only a subset of evaluators has submitted marks. It encodes accountability by writing activity log entries for login events, interview starts, score submissions, screening actions, and selection confirmations. It encodes confidentiality by storing password hashes rather than plaintext credentials and by serving uploaded documents through controlled endpoints.",
        "User interface copy reinforces values in subtle ways. Interviewer portals instruct panel members to wait when HR has not yet started the next candidate, reducing premature evaluations. HR dashboards label pending evaluators by name so that follow-up can be targeted rather than broadcast. These design elements collectively shape behaviour toward institutional standards.",
    ],
    "1.6 System Request": [
        "The formal request document also referenced compliance with organisational IT policies requiring deployment within approved infrastructure and adherence to branding guidelines issued by corporate communications. The development team reviewed available logo assets and colour specifications before finalising cascading style sheets shared across portals.",
    ],
    "1.7 Problem Definition": [
        "Quantifying the problem space, HR stakeholders estimated that manual collation of interview marks for a single senior panel could consume two to four staff-hours per candidate when multiple evaluators and document formats were involved. Scheduling conflicts arising from email-based coordination reportedly delayed some interview rounds by several weeks. Applicant complaints occasionally cited uncertainty about whether applications had been received—an issue addressable through immediate on-screen confirmation and email acknowledgements where SMTP is enabled.",
        "Problem definition also considered failure modes: lost files, inconsistent shortlisting criteria between recruitment campaigns, and inability to reproduce scoring calculations during audits. Each failure mode maps to a mitigating feature in the proposed system, providing traceability from problem statement to solution component.",
    ],
    "1.8 Aim and Objectives": [
        "Each objective was assigned acceptance criteria during analysis. For example, the interviewer portal objective was considered satisfied when external users could authenticate with name and access code, view only the active candidate, submit marks, and see updates after HR started subsequent candidates. The screening objective required demonstration that screening requests were rejected until all panel members had submitted marks for all interviewed candidates, and that ranking used arithmetic mean of evaluator totals.",
    ],
    "1.9 Justification": [
        "Comparative analysis with commercial SaaS applicant tracking products indicated licensing models priced per recruiter or per vacancy that could exceed institutional software budgets when extrapolated over multiple years. A custom solution incurs higher initial development effort but eliminates recurring licence fees and permits unlimited customisation aligned with GMB-specific interview practices, including external board members and multi-criteria mark sheets.",
    ],
    "1.10 Chapter Summary and Conclusion": [
        "Chapter One therefore establishes the conceptual and practical rationale for the project. Subsequent chapters should be read as consecutive layers of specification and realisation, each dependent on the foundations laid here.",
    ],
    "2.1 Introduction to Project Planning": [
        "Planning also encompassed documentation deliverables required for academic assessment, including this formal report, user-facing setup guides, and technical README materials. Alignment between academic milestones and software milestones was maintained through a Gantt-style schedule reviewed at supervision meetings.",
    ],
    "2.2 Project Scope": [
        "Boundary decisions excluded integration with biometric attendance systems or payroll, which belong to post-hire processes. However, export of selected candidate data in CSV format was retained within scope to support manual handoff to onboarding teams until automated integration becomes available.",
    ],
    "2.3 Stakeholder Identification and Engagement": [
        "Conflict resolution mechanisms were defined for disagreements over feature priority. When HR requested additional reporting widgets late in development, the change control board assessed impact on stability and deferred non-critical analytics to a future release, preserving on-time delivery of hiring workflows.",
    ],
    "2.4 Project Timeline and Development Phases": [
        "Milestone reviews at the end of each phase produced go/no-go decisions. The analysis phase could not conclude until requirements were signed off by HR representatives. The design phase required approval of wireframes for dashboard navigation. Implementation milestones included demonstration of end-to-end application from job posting through selection.",
    ],
    "2.5 Resource Planning": [
        "Hardware redundancy was considered for production deployment, recommending at minimum off-server backup of data and uploads directories nightly. Development machines utilised virtual environment isolation to prevent dependency conflicts between project and system Python packages.",
    ],
    "2.6 Risk Management": [
        "A risk register was reviewed fortnightly. High-probability risks near deployment included interviewer non-participation; mitigation involved HR reminder workflows and visible pending-evaluator lists. Low-probability but high-impact risks such as server compromise were mitigated through access control recommendations documented in deployment guidance.",
    ],
    "2.7 Feasibility Study": [
        "Schedule feasibility benefited from reuse of existing HTML templates and CSS assets from earlier prototyping efforts, reducing frontend effort. Technical feasibility of CV scoring was validated with sample curriculum vitae files representing diverse formats encountered in prior recruitment campaigns.",
    ],
    "2.8 Project Management Methodology": [
        "Daily development logs captured completed routes, templates modified, and defects resolved. This practice supported accurate progress reporting and facilitated resumption after interruptions.",
    ],
    "2.9 Chapter Summary": [
        "Effective planning reduced rework during implementation and provided stakeholders with realistic expectations regarding prototype capabilities versus future enhancements.",
    ],
    "3.1 Introduction to Systems Analysis": [
        "Analysis deliverables included narrative use cases, a logical entity-relationship perspective, and prioritised requirement lists classified as must-have, should-have, and could-have. Must-have items encompassed application capture, HR login, interview scheduling, and multi-evaluator scoring.",
    ],
    "3.2 Analysis of the Existing System": [
        "Process observation revealed that HR officers maintained personal spreadsheets tracking interview dates alongside official registers, creating version control problems. Interview panel chairs occasionally aggregated scores in personal notebooks before dictating results to secretaries—a bottleneck and error source eliminated by digital per-evaluator submissions.",
    ],
    "3.3 Requirements Gathering Techniques": [
        "Questionnaires were distributed to a small sample of recent applicants asking about preferred application channels; responses favoured online submission with immediate confirmation. This finding reinforced investment in the public portal rather than PDF-only application forms.",
    ],
    "3.4 Functional Requirements": [
        "Detailed functional requirements were numbered for traceability. Authentication requirements specify lockout policies optional for future releases. Reporting requirements include CV analysis CSV export endpoints for HR analytics. Bulk email capabilities support communication with multiple shortlisted or rejected candidates subject to template configuration.",
    ],
    "3.5 Non-Functional Requirements": [
        "Availability requirements for prototype demonstration target ninety-five percent during business hours on local hosting. Backup requirements specify weekly full copies of data directory. Localization requirements currently support English language interfaces with extensibility for additional languages through template externalisation in future.",
    ],
    "3.6 Data Analysis and Entity Identification": [
        "Attribute dictionaries document field types and validation rules. Application email fields require format validation. Interview marks require integer bounds between zero and twenty per criterion. Job due dates must parse ISO datetime formats for deadline state computation distinguishing open and closed vacancies.",
    ],
    "3.7 Business Process Analysis": [
        "Swimlane descriptions clarify responsibilities: applicants submit, HR screens and schedules, interviewers evaluate active candidates only, HR screens aggregates when complete, HR manager confirms selection. Exception flows handle no-show cancellations, queue removals with mandatory reasons, and rejection emails with optional messaging.",
    ],
    "3.8 Gap Analysis": [
        "Residual gaps after implementation may include absence of native mobile apps and limited business intelligence dashboards; these are documented as future enhancements rather than oversights.",
    ],
    "3.9 Chapter Summary": [
        "Thorough analysis reduced ambiguity prior to design, preventing costly architectural reversals during coding.",
    ],
    "4.1 Introduction to System Design": [
        "Design reviews evaluated alternative architectures including separate single-page applications for each portal versus server-rendered templates. Server-rendered Jinja2 templates were selected for faster development, simpler deployment, and easier branding consistency without complex cross-origin configurations.",
    ],
    "4.2 System Architecture": [
        "Layered separation ensures templates contain minimal business logic, with complex decisions residing in Python functions testable independent of HTML rendering. JSON APIs return structured responses consumed by JavaScript fetch calls on HR dashboard for interviewer management and mark saving without full page reloads where appropriate.",
    ],
    "4.3 Database and Data Structure Design": [
        "Migration scripts conceptually map JSON structures to relational tables with foreign keys enforcing referential integrity. Interview score submissions may normalise into child tables linked by application_id and scorer_id composite uniqueness constraints.",
    ],
    "4.4 User Interface and Experience Design": [
        "Usability heuristics guided placement of primary actions: Start and Score buttons appear adjacent to candidate rows in interview tables; destructive actions such as Remove from Queue require modal confirmation with mandatory reason textareas to prevent accidental data loss.",
    ],
    "4.5 Module Design": [
        "Inter-module dependencies were minimised. CV scoring does not depend on interview modules. Email service depends only on settings and templating utilities. Interviewer panel logic depends on user records and job identifiers but not on audit modules, though audit logs capture resulting events.",
    ],
    "4.6 Security Design": [
        "Threat modelling considered unauthorised access to uploads directory. Direct file URLs require knowledge of generated filenames; HR resume routes additionally verify authenticated sessions. Interviewer tokens expire after twenty-four hours reducing window for link sharing abuse.",
    ],
    "4.7 Interview Panel and Sequential Workflow Design": [
        "Polling interval of five seconds on interviewer dashboards balances responsiveness with server load. Alternative push-based designs using WebSockets were deferred due to deployment complexity on constrained hosting environments.",
    ],
    "4.8 Curriculum Vitae Scoring Design": [
        "Skill keyword lists are extensible in services/cv_scoring.py to reflect sector-specific competencies such as grain storage management, commodity trading regulations, or agricultural economics qualifications relevant to GMB roles.",
    ],
    "4.9 Email System Design": [
        "HTML email templates embed institutional colours and logo for professional appearance. Plain-text fallbacks may be added in future for clients blocking HTML rendering.",
    ],
    "4.10 Chapter Summary": [
        "Design documentation served as the authoritative reference during implementation disputes, reducing ad hoc coding deviations.",
    ],
    "5.1 Introduction to Implementation": [
        "Implementation followed bottom-up sequencing: data layer helpers, authentication, applicant routes, HR routes, interviewer routes, then polish and documentation. Continuous manual testing accompanied each merged feature branch.",
    ],
    "5.2 Development Environment and Tools": [
        "Virtual environment venv isolated project dependencies. Requirements pinning captured versions tested during development to reproduce builds on other machines. Editor configurations included Python linting and template syntax highlighting.",
    ],
    "5.3 Implementation of Core Modules": [
        "Context processor inject_user supplies templates with current_user, permission flags, portal_logo_src, company_display_name, and welcome media variables enabling consistent headers without repeating boilerplate across dozens of template files.",
    ],
    "5.4 Implementation of Interview and Scoring Logic": [
        "Helper function _candidate_full_name standardises display names avoiding duplication when surname already appears in name field. Function _json_safe prepares application dictionaries for JavaScript embedding in templates without serialisation errors on datetime objects.",
    ],
    "5.5 Testing": [
        "Regression testing repeated core flows after each significant change. Particular attention was paid to interview status transitions after feedback that premature completion labels had confused HR users during pilot demonstrations.",
    ],
    "5.6 Deployment Considerations": [
        "Production checklist items include changing default HR and audit passwords, configuring HTTPS certificates, disabling Flask debug mode, and establishing monitoring for disk usage as uploads accumulate.",
    ],
    "5.7 Challenges and Solutions": [
        "Interviewer access code migration required backfilling panel records for legacy data created before one-time code feature introduction. Load-time migration in load_all_data addressed schema drift without manual JSON editing.",
    ],
    "5.8 Chapter Summary and Overall Conclusion": [
        "The implemented artefact satisfies academic and organisational objectives by demonstrating full-stack competency and delivering a deployable recruitment prototype. Continued partnership between HR and IT will determine the pace of production rollout and identification of the next prioritised enhancement backlog items.",
    ],
}

# Long-form additional sections for page count
EXTRA_SECTIONS_CH3 = {
    "3.10 Use Case Narratives": [
        "Use case UC-01 describes an applicant discovering a Chief Executive Officer vacancy on the careers portal, reviewing job requirements, uploading a curriculum vitae in DOCX format, and receiving on-screen confirmation of successful submission. The system validates email format, checks for duplicate applications, stores the document under uploads with a unique filename, and creates an application record with pending status.",
        "Use case UC-02 describes an HR officer screening applications after a vacancy closes. The officer selects the job in the screening section, executes automated scoring, reviews ranked results with matched and missing skills displayed, and advances selected candidates to interview status. Manual override remains possible for edge cases requiring human discretion.",
        "Use case UC-03 describes external interview panel operations. HR adds two interviewers, generates shared link and access code, and distributes credentials. HR starts the first candidate's interview. Both interviewers log in, see only that candidate, submit marks, and observe pending evaluator counts update. HR starts the second candidate; interviewer browsers refresh automatically. After all candidates receive complete marks, HR screens and selects top averages.",
    ],
}

EXTRA_SECTIONS_CH4 = {
    "4.11 Interface Mock-up Description": [
        "The HR dashboard sidebar uses teal background with orange highlight on active navigation items. The interview marks section presents a candidate picker and criteria grid with rows per evaluator and a highlighted average row. Colour coding indicates pending evaluators in amber and completed interviews in green.",
        "The applicant index page features a hero section with optional welcome video, benefit bullet points, and searchable job grid. Cards display job title, department, deadline badge, and apply button. Closed jobs are filtered from public view based on deadline_state computation.",
    ],
}

EXTRA_SECTIONS_CH5 = {
    "5.9 Implementation Screens and Evidence": [
        "Screenshot evidence for academic submission should be captured from running localhost instance showing applicant portal, HR dashboard interview section, interview marks table with multiple evaluator rows, interviewer active candidate view, and settings branding upload panel. Images should be stored under docs/images with descriptive filenames as documented in project setup guides.",
        "Code evidence includes representative excerpts from app.py demonstrating route definitions, permission decorators, and score averaging functions. Services/cv_scoring.py excerpts illustrate text extraction and similarity computation. These artefacts may be appended to presentation slides or viva voce materials supplementing this written report.",
    ],
}

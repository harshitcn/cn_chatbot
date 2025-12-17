"""
Static FAQ data storage.
Contains a list of question-answer pairs for the chatbot.
"""
from typing import List, Dict

"""
q: are u a parent or owner

"""




# FAQ data structure: List of dictionaries with 'question' and 'answer' keys
FAQ_DATA: List[Dict[str, str]] = [
    {
        "question": "What is Code Ninjas and how does the franchise model work?",
        "answer": "Code Ninjas is a STEM learning center where kids learn coding, robotics, and game development through a structured, belt-based curriculum. Franchise owners operate a physical learning center supported by centralized curriculum, systems, and marketing assets."
    },
    {
        "question": "What are the benefits of owning a Code Ninjas franchise?",
        "answer": "Benefits include a proven curriculum, strong brand recognition, dedicated franchise support teams, comprehensive software systems, and a structured operational lifecycle (onboarding → support → expansion → transfer/closure). (The operations structure is evident in the Closure Manual's multi-department workflows)."
    },
    {
        "question": "Do I need coding or teaching experience?",
        "answer": "No. Code Ninjas provides curriculum, training, and operational guidance. Owners manage the business and hire instructors (Senseis)."
    },
    {
        "question": "How much does it cost to open a Code Ninjas center?",
        "answer": "Investment varies by market, build-out, and size. Exact cost ranges, royalties, and financial disclosures are outlined in the Franchise Disclosure Document (FDD)."
    },
    {
        "question": "How long does it take to open a center?",
        "answer": "Typically 3–9 months depending on site approval, build-out, hiring, permitting, and onboarding."
    },
    {
        "question": "What kind of support does Code Ninjas provide?",
        "answer": "Support includes: Training (owners + staff), Curriculum delivery, Marketing launch assistance, Technology setup (Dojo, M365, MyStudio, etc.), Ongoing operations coaching, Software, branding, and compliance management. The structured cross-departmental process is reflected in items shown in the Closure Process Manual (Tech, Marketing, HO, Legal, etc.)."
    },
    {
        "question": "How do I raise a support issue?",
        "answer": "To raise a support issue, please contact your Franchise Business Partner (FBP) or reach out to the Code Ninjas support team. You can submit a support ticket through the franchise portal, email the support team directly, or call the support hotline. For urgent issues, please contact your FBP immediately. The support team will assist you with technical issues, operational questions, system access problems, and other concerns related to your franchise operations."
    },
    {
        "question": "I want to raise a support issue",
        "answer": "To raise a support issue, please contact your Franchise Business Partner (FBP) or reach out to the Code Ninjas support team. You can submit a support ticket through the franchise portal, email the support team directly, or call the support hotline. For urgent issues, please contact your FBP immediately. The support team will assist you with technical issues, operational questions, system access problems, and other concerns related to your franchise operations."
    },
    # {
    #     "question": "What Code Ninjas centers are currently for sale?",
    #     "answer": "Center resale opportunities vary by region and availability. Franchise Development can provide the current list of active resale markets after you submit a franchise inquiry."
    # },
    {
        "question": "How can I find out which centers I can buy?",
        "answer": "Once you complete the inquiry form, a Franchise Development Manager will guide you through available resale opportunities that fit your preferred geography, budget, and ownership goals."
    },
    {
        "question": "Can I request information about a specific center that I know is for sale?",
        "answer": "Yes. You may request details on a specific center, and the team can share general information—full financials and operational data require an NDA and FDD review."
    },
    # {
    #     "question": "Is buying an existing center different from opening a new one?",
    #     "answer": "Yes. Buying a resale generally allows you to: Acquire an established customer base, Take over trained staff and existing operations, Begin earning revenue immediately, Avoid build-out costs. New centers allow more customization but require time to build membership."
    # },
    {
        "question": "What steps are involved in buying an existing center?",
        "answer": "The process typically includes: Inquiry submission, FDD review and NDA signing, Review of financials and operations, Seller meetings and validation, Approval by Franchise Development, Transfer process, including systems handoff, legal documents, and onboarding. (The lifecycle and departmental involvement for transfers mirrors aspects shown in the Closure/Operations manual workflows.)"
    },
    {
        "question": "What support do I get when taking over an existing center?",
        "answer": "You receive: Transition support, System onboarding, Marketing guidance, Curriculum training, Tech and operational setup assistance."
    },
    {
        "question": "How can I open a brand-new Code Ninjas center?",
        "answer": "Submit a franchise inquiry → meet your Franchise Development Manager → review the FDD → secure a territory → sign the Franchise Agreement → begin site selection and onboarding."
    },
    {
        "question": "How do you determine if my territory is available?",
        "answer": "Territories are mapped based on population, demand, and proximity to existing centers. Franchise Development will confirm whether your preferred geography is open, reserved, or at capacity."
    },
    {
        "question": "Can I choose any location to open my center?",
        "answer": "Location approval must meet Code Ninjas' criteria for: Demographics, Accessibility, Foot traffic, Safety, Market demand. Your team will guide you through site selection and lease review."
    },
    {
        "question": "What tools and systems do new centers receive?",
        "answer": "You receive access to: Dojo (curriculum + student progression), CRM and membership systems, Marketing templates, Operations manuals, Technology licensing and account provisioning. These systems are maintained and updated by specialized internal teams (as reflected in the Tech and Marketing steps in the Closure Manual)."
    },
    {
        "question": "How many employees do I need to operate?",
        "answer": "Most centers require: 1 Center Director, A team of part-time Senseis, Optional administrative support (depending on volume)."
    },
    {
        "question": "What are the main revenue streams for new centers?",
        "answer": "New centers typically earn through: Monthly memberships, STEM camps, Workshops, Parents' Nights Out events, Special programs and partnerships."
    },
    {
        "question": "How do I know if my city or zip code is available?",
        "answer": "A Franchise Development Manager will check territory maps and confirm availability once you submit an inquiry."
    },
    {
        "question": "Are multi-unit ownership opportunities available?",
        "answer": "Yes. Strong candidates with business experience often qualify for owning 2–5 centers, depending on market capacity."
    },
    {
        "question": "What qualifications do I need to be approved?",
        "answer": "Typical requirements include: Financial capability to invest, Community-oriented mindset, Ability to lead staff, Willingness to follow franchise systems, Strong communication and customer experience focus."
    },
    {
        "question": "What ongoing fees should I expect?",
        "answer": "The FDD outlines all recurring fees, including: Royalties, Marketing fund contributions, Tech/platform fees."
    },
    {
        "question": "Do you provide financing?",
        "answer": "Many franchisees use SBA loans, third-party financing partners, or personal funding. Code Ninjas does not directly finance centers."
    },
    {
        "question": "When do I receive the FDD?",
        "answer": "You receive the Franchise Disclosure Document after your initial qualification call with Franchise Development."
    },
    {
        "question": "What if I need to close my center in the future?",
        "answer": "Code Ninjas has a clear, multi-departmental closure and compliance process with support from Accounts, Legal, HO, Tech, Marketing, and Post-Ops, ensuring owners are not left alone during lifecycle transitions."
    },
    {
        "question": "What centers are currently available for resale?",
        "answer": "Resale opportunities change frequently. Once you submit a franchise inquiry, our Franchise Development team will share the current list of Code Ninjas centers that are available for purchase and help you evaluate which ones fit your goals and geography."
    },
    # {
    #     "question": "Which centers can I buy?",
    #     "answer": "Subject to approval, you can purchase any center that: is officially listed for resale, and meets Code Ninjas standards for financial and operational standing, and is in a territory you are approved to own. Your Franchise Development Manager will walk you through which centers are open for purchase and what is required to become the approved buyer."
    # },
    {
        "question": "How is buying an existing center different from opening a new one?",
        "answer": "Buying an existing center usually means: an established student base and revenue, existing staff and systems already in place, a defined operating history you can review. Opening a new center usually means: more upfront build-out and ramp-up work, you're starting enrollment from zero, more flexibility to shape local relationships from day one. Both options follow a structured approval and onboarding process."
    },
    # {
    #     "question": "What is the process to buy an existing Code Ninjas center?",
    #     "answer": "While details vary, the typical steps are: Submit inquiry and initial qualification, Review FDD and sign necessary confidentiality documents, Receive high-level center information and financials, Speak with the seller and existing team (where appropriate), Secure Code Ninjas' approval as a new franchisee, Complete transfer documents and training, Transition operational systems and accounts through our internal transfer/closure tools involving Accounts, Legal, Tech, Marketing, HO and Post-Ops."
    # },
    {
        "question": "Can I sell my Code Ninjas franchise in the future?",
        "answer": "Yes. Subject to the Franchise Agreement and Code Ninjas approval, you may sell your center to a qualified buyer. Code Ninjas supports a structured transfer process designed to protect students, the brand, and both buyer and seller."
    },
    # {
    #     "question": "How do I start the process if I want to sell my center?",
    #     "answer": "You'll typically: Inform Franchise Development/Support that you'd like to pursue a sale, Review transfer requirements in your Franchise Agreement and FDD, Identify potential buyers (sometimes already in your local network), Work with Code Ninjas to qualify and approve the buyer, Use the internal Transfer tools and workflows to manage financial, legal, and operational handoff (including accounts, systems, and marketing assets)."
    # },
    {
        "question": "What does Code Ninjas do to help with a sale or transfer?",
        "answer": "Internally, Code Ninjas uses dedicated Transfer, Closure, and Termination modules and checklists that: coordinate Accounts, Legal, HO, Tech, Marketing and Post-Ops, ensure contracts, fees, and system access are correctly updated, help manage communications, documentation, and important dates. From a seller's point of view, that means the brand has a formal, guided process rather than leaving you to figure it out alone."
    },
    {
        "question": "Can I transfer my franchise to a family member or business partner?",
        "answer": "Yes, in many cases ownership can be transferred to a qualified family member or partner, subject to Code Ninjas' approval and the requirements in your Franchise Agreement. This follows the same structured transfer workflow (background checks, training, updated documents, and system changes)."
    },
    {
        "question": "Will my staff and students stay with the center after a sale?",
        "answer": "The goal is continuity. Most transfers are structured so the center keeps operating with minimal disruption for families and staff. The buyer and seller work together, with Code Ninjas' guidance, on transition planning, communication, and timing."
    },
    {
        "question": "What is the difference between a closure and a termination?",
        "answer": "A closure is typically a business decision initiated by the owner (for example, at the end of the Franchise Agreement term or for strategic/financial reasons). A termination usually refers to ending the Franchise Agreement early because of a default or serious non-compliance, and often involves legal rights and remedies. Both have formal, multi-department processes."
    },
    # {
    #     "question": "If I decide to close when my term ends, what happens?",
    #     "answer": "If you choose not to renew at the end of your agreement or to close voluntarily, Code Ninjas uses its Closures process to coordinate: final financial reconciliation and QBO updates (Accounts), legal releases and documentation (Legal, HO), turning off tech systems (Tech: Dojo, CRM, M365, etc.), updating marketing, web presence, and listings (Marketing/Canva/Social), managing post-operations items like physical signage and location status (Post-Ops). This is designed to be orderly and compliant, with clear checklists and status tracking."
    # },
    {
        "question": "Will Code Ninjas help manage communication with families if I close?",
        "answer": "Yes. The Closure process includes steps for franchisees to inform customers and confirm that communication has occurred before the closure is finalized. This is tracked as part of the internal checklist and status updates."
    },
    {
        "question": "Can I close one location and keep another?",
        "answer": "In multi-unit ownership, closures are handled by location. You may, in some cases, close or not renew one center while keeping others, subject to your agreements and overall performance requirements."
    },
    {
        "question": "Are there fees or obligations when I close?",
        "answer": "Your FDD and Franchise Agreement will outline any fees or remaining obligations associated with non-renewal or early closure (e.g., outstanding amounts, lease responsibilities, equipment, and post-term covenants). The internal Accounts and Legal teams confirm these as part of the Closure workflow."
    },
    {
        "question": "Under what circumstances could my Franchise Agreement be terminated?",
        "answer": "Termination is generally associated with serious or ongoing breaches of the Franchise Agreement—such as non-payment, non-compliance with brand standards, or legal/regulatory issues. Specific grounds and cure periods are detailed in the FDD and Franchise Agreement, not in marketing materials."
    },
    {
        "question": "How is a termination handled if it happens?",
        "answer": "Code Ninjas uses a dedicated Terminations module that: records key dates and details, routes the request through Accounts, Legal, HO, Tech, Marketing, Post-Ops, and Support, tracks completion of tasks like financial reconciliation, system deactivation, marketing removal, and physical location actions. Each department's status is monitored and must be completed before the termination is fully processed."
    },
    {
        "question": "Will I be informed of what I need to do during a termination process?",
        "answer": "Yes. Internally, the Terminations process uses checklists, automated emails, and status dashboards so that owners and departments know what steps are required and when they're completed. For you as an owner, this means a clear, guided path even in difficult scenarios."
    },
    {
        "question": "How does Code Ninjas ensure legal and regulatory compliance during closure or termination?",
        "answer": "Legal and HO teams are explicitly part of both Closure and Termination workflows. They review documentation, ensure required notices are given, and verify that legal steps are completed before the process is marked as finished."
    },
    {
        "question": "Can I see the full details of these processes before I sign?",
        "answer": "Yes. While the internal tools themselves are not public, the rights, obligations, and procedures for closure, transfer, and termination are fully described in the FDD and Franchise Agreement. Prospective owners review these documents during the discovery process and can consult their own advisors."
    },
    {
        "question": "What do these internal Closure and Termination processes mean for me as a prospective owner?",
        "answer": "They show that Code Ninjas has formal, documented, and system-supported ways to handle: voluntary exits, resales and transfers, non-renewal at end of term, serious compliance issues. Multiple departments—Accounts, Legal, HO, Tech, Marketing, Canva, Post-Ops, FranDev, Support—are coordinated via internal checklists, email triggers, and status tracking so that you're supported throughout the full lifecycle of your business, not just at opening."
    },
    {
        "question": "What are my realistic exit options as a Code Ninjas franchise owner?",
        "answer": "You generally have three paths: Sell/transfer your center to a qualified buyer, Non-renew or voluntarily close at the end of your term, or In rare cases, face termination for serious non-compliance. Code Ninjas has dedicated Closure and Termination processes in its internal web app to manage each of these options in a structured, multi-department way (Accounts, Legal, HO, Tech, Marketing, Post-Ops, etc.)."
    },
    {
        "question": "If I invest, how long is my commitment and what happens at the end of the term?",
        "answer": "Your Franchise Agreement covers a fixed initial term (and possible renewals); the exact years are in the FDD. Toward the end of the term, you can: Apply to renew (subject to performance and brand standards), Sell/transfer to an approved buyer, or Close the center following the formal Closure process."
    },
    {
        "question": "How can I buy an existing Code Ninjas center?",
        "answer": "After you submit a franchise inquiry and pass initial qualification, Franchise Development will share current resale opportunities. If you and the center are a mutual fit, you'll review the FDD, sign any needed NDAs, evaluate financials, and go through approval and training before ownership is formally transferred in the internal Transfer/Closure tools."
    },
    {
        "question": "How do I know which centers are actually for sale and which ones I'm allowed to buy?",
        "answer": "Resale status changes frequently and is not always fully public. Once you're in the pipeline, Franchise Development will confirm: Which centers are officially on the market, Whether the territory is open to you (no conflicts), and Whether you meet the financial/experience criteria to be the approved buyer."
    },
    {
        "question": "What's the operational difference between buying an existing center and opening a new one?",
        "answer": "Buying an existing center means you inherit an operating business with current students, staff, systems, and historical financials. Opening new means you build from zero: site build-out, initial staffing, and enrollment ramp-up. Both paths still go through Code Ninjas' structured onboarding and system setup (Dojo, CRM, M365, etc.)."
    },
    {
        "question": "When I buy an existing center, how is the handover of systems and obligations controlled?",
        "answer": "The same internal platforms used for Closures and Terminations are used to coordinate financial updates, legal documents, software access (Dojo, MyStudio, M365), marketing assets, and physical location items. Each department has checklist items and status indicators (yellow/green/grey) so nothing critical is missed during the transfer."
    },
    {
        "question": "If I want to sell my center one day, what does Code Ninjas require?",
        "answer": "You'll need to: Notify Franchise Development of your intent to sell, Find a buyer who meets Code Ninjas' financial and experience standards, Allow time for approval, training, and legal documentation, and Participate in a structured transfer process so accounts, systems, fees, and branding are cleanly handed over using the internal workflows."
    },
    {
        "question": "Can I transfer the franchise to a family member or partner instead of an outside buyer?",
        "answer": "Yes, in most cases transfers to family or partners are possible, but they must still be approved franchisees: meeting financial criteria, completing training, and signing updated agreements. Internally, this is treated like any other Termination/Transfer event with Accounts, Legal, Tech, Marketing, and Post-Ops each completing their parts."
    },
    {
        "question": "How will my families and staff be protected during a sale or transfer?",
        "answer": "The internal processes were built to avoid \"messy\" transitions. They require confirmation that: Parents are informed appropriately, Systems access changes at the right time, Branding and communications are updated, and Financial/QBO data are correctly reconciled."
    },
    {
        "question": "What happens if I choose to close my center at the end of the agreement instead of renewing?",
        "answer": "You'll work with your Franchisee Business Partner (FBP) to initiate a Closure record for your location. Once submitted, it automatically routes tasks through Accounts, Legal, HO, Tech, Marketing, Canva, and Post-Ops to manage: damages/fees, signed documents, software deactivation, website/listing updates, and physical location shutdown."
    },
    {
        "question": "How structured is the closure process if I exit voluntarily?",
        "answer": "Very structured. The Closure app includes: Mandatory data fields (location, FA details, owner contact, dates), A checklist of prerequisites per department, Automated emails to each team, and Color-coded status indicators (yellow in progress, green completed, grey no updates) so progress is visible at a glance."
    },
    {
        "question": "Will Code Ninjas help manage communication with parents if my center is closing?",
        "answer": "Yes. Closure tasks specifically include informing customers and updating FranConnect and marketing channels. You must confirm in the system that families were notified before the closure can progress, ensuring a controlled and respectful wind-down."
    },
    {
        "question": "In what situations could my Franchise Agreement be terminated rather than closed normally?",
        "answer": "Termination typically occurs when there are serious or repeated breaches of the Franchise Agreement (for example, continued non-payment, severe brand standards violations, or legal issues). The specific grounds and cure periods are spelled out in the FDD and Franchise Agreement; they are not arbitrary."
    },
    # {
    #     "question": "How is a termination operationally handled if it happens?",
    #     "answer": "A termination is logged in the Terminations segment of the internal app. The FBP initiates it, and then Accounts, Legal, HO, Tech, Marketing, Soci, Canva, FranDev, Post-Ops, and Support all receive automated tasks and emails to: Reconcile QBO and any damages/payment terms, Update legal status and documents, Turn off software and accounts, Remove marketing and signage, and Document the state of the physical location."
    # },
    # {
    #     "question": "What are the biggest operational challenges Code Ninjas owners face, especially in the first few years?",
    #     "answer": "Most new owners face three core challenges: Staffing consistency — Hiring and keeping strong Senseis and a dependable Center Director is one of the heaviest levers of success. Instructor turnover creates retraining costs, disrupts quality, and increases your time in the center. Enrollment momentum — The model relies on consistent marketing, community engagement, and school partnerships. Owners who expect \"if you build it, they will come\" struggle. Time investment — Even semi-absentee owners must expect to be hands-on early, especially during launch, major staffing changes, or seasonal shifts. The top-performing owners lean into community visibility and make hiring a constant, not reactive, process."
    # },
    # {
    #     "question": "What separates the most successful Code Ninjas centers from the average ones?",
    #     "answer": "High performers consistently: Treat their Center Director as their #1 hire and invest in leadership stability, Track KPIs weekly (retention, new enrollments, belt progression, payroll %, marketing performance), Proactively recruit Senseis so turnover never becomes an emergency, Show up in their community — school partnerships, STEM fairs, local events, Run camps aggressively and use them as a feeder for memberships, Follow operational playbooks rather than \"winging it\". These behaviors matter more than the market itself."
    # },
    # {
    #     "question": "What are the most common reasons a center struggles or eventually closes?",
    #     "answer": "Patterns across the system show a combination of: Weak staffing (especially turnover in Center Directors), Inconsistent marketing, Lack of owner engagement, Late intervention on operational issues, Cash-flow mismanagement during slow seasons, Avoidance of brand-required standards. Most closures are not sudden — they follow months of stagnation and lack of active correction."
    # },
    # {
    #     "question": "How long does it typically take a new center to reach break-even?",
    #     "answer": "While results vary by location and management, many centers need 6–18 months to reach break-even. Key factors include: Rent and build-out cost, Speed of staffing, Strength of launch marketing, Camp performance, The Center Director's capability. Centers that open strong with robust pre-launch efforts often ramp up faster."
    # },
    # {
    #     "question": "What are the biggest unexpected expenses new owners should plan for?",
    #     "answer": "Higher-than-expected payroll during peak times, Extra marketing pushes to boost enrollment, Replacing or supplementing IT equipment, Instructor retraining from turnover, Seasonal revenue dips (e.g., December, late summer). Owners who budget conservatively and assume fluctuations avoid cash-flow crunches."
    # },
    # {
    #     "question": "How stable is the revenue stream? Does enrollment fluctuate a lot?",
    #     "answer": "Membership revenue is relatively stable once you reach a healthy base, but centers do experience seasonal rhythms. Camps can significantly boost summer revenue, but membership may dip during holidays. Owners who run year-round engagement programs (events, competitions, partnerships) maintain stronger retention."
    # },
    # {
    #     "question": "What types of markets or territories perform the strongest?",
    #     "answer": "The strongest territories share common traits: High concentration of families with school-aged children, Affluent or middle-class demographics, School districts receptive to after-school programs, Competition in STEM being present but not oversaturated, Communities with active parent networks. The location inside the territory matters as much as the territory itself."
    # },
    # {
    #     "question": "What are red flags that a territory might not be a good fit?",
    #     "answer": "Very low population density, Highly rural communities with long travel distances, Markets where after-school enrichment spending is low, Locations without accessible retail/education corridors, Landlords offering poor visibility or restrictive leases. Good territories still need good site selection."
    # },
    # {
    #     "question": "How hard is it to hire and keep Senseis?",
    #     "answer": "Hiring Senseis is manageable but requires ongoing effort. Most centers hire college students or tech enthusiasts, which means turnover is natural. Owners who build a bench — continuously interviewing, maintaining connections, and offering strong center culture — avoid disruption."
    # },
    # {
    #     "question": "How critical is the Center Director role?",
    #     "answer": "It is one of the most important roles in the business. A strong Director contributes to: Retention, Customer satisfaction, Instructor performance, Event quality, Operational discipline, Marketing execution. A weak Director is the #1 predictor of underperformance."
    # },
    # {
    #     "question": "What does Code Ninjas support look like day to day?",
    #     "answer": "You'll receive: A dedicated Franchise Business Partner (FBP), Access to operational guides, curriculum updates, and marketing assets, Support tickets for tech and system issues, Launch support for grand openings and new programs, Structured pathways for escalations, Technology setup and shutdown processes that involve specialized teams. Support is designed to keep owners focused on operations rather than admin complexity."
    # },
    # {
    #     "question": "How stable and reliable are the systems (Dojo, CRM, M365, etc.)?",
    #     "answer": "The systems are mature and actively maintained. As with any SaaS stack, occasional issues occur, but Code Ninjas' tech and operations teams coordinate system access and updates across all lifecycle stages — onboarding, growth, and even closure/termination workflows (as shown in internal manuals). This multi-team oversight improves reliability and transparency."
    # },
    # {
    #     "question": "What should I ask when evaluating an existing center for purchase?",
    #     "answer": "Ask for: Retention trends (not just enrollments), Payroll percentage, Belt progression health (indicator of customer satisfaction), Stability of the Center Director and key staff, Historical camp performance, Lease terms and remaining years, Any upcoming operational or compliance requirements. The goal is to understand momentum, not just raw numbers."
    # },
    # {
    #     "question": "How do I know if the seller's center is healthy or on the decline?",
    #     "answer": "Look at: Month-over-month active students, Staff turnover, Negative parent reviews, Belt stagnation, Declining camp turnout, Payroll spikes, Reduced community events. A healthy center has forward motion; a declining center shows disengagement."
    # },
    # {
    #     "question": "How difficult is it to sell a Code Ninjas center when the time comes?",
    #     "answer": "Saleability depends on the center's performance, staff stability, lease situation, and operational cleanliness. The brand facilitates the process through a structured, multi-department transfer workflow — but buyer demand depends on performance, not just brand strength."
    # },
    # {
    #     "question": "What does Code Ninjas do to ensure a smooth sale or transfer?",
    #     "answer": "Internal transfer processes (similar to closure workflows) coordinate: Financial reconciliation, Legal documentation, Software access changes, Marketing updates, Physical location tasks. This avoids messy handovers and protects the brand, staff, and families."
    # },
    # {
    #     "question": "Why do some centers close or get terminated?",
    #     "answer": "Closures generally happen when: The owner does not renew at the end of term, Personal circumstances change, The business never reached stable enrollment, Lease costs were too high, The owner disengaged from operations. Terminations happen far less often and usually involve: Chronic non-payment, Repeated non-compliance with brand standards, Safety or legal violations, Ignoring required corrective actions."
    # },
    # {
    #     "question": "If something goes wrong, how supported am I through closure or termination?",
    #     "answer": "Code Ninjas has a formal, documented process involving all key departments: Accounts, Legal, HO, Tech, Marketing, Canva, Soci, Post-Ops, Support. This ensures: Systems are shut down properly, Families are informed, Financial and legal steps are completed, Branding and IT are responsibly wrapped up. It's clear, structured, and transparent — no ambiguity."
    # },
    # {
    #     "question": "What traits do the most successful Code Ninjas owners share?",
    #     "answer": "They tend to: Enjoy being present in their community, Embrace a service-and-education style business, Treat staff leadership as their #1 job, Operate with consistency and discipline, Stay curious and adaptable, Engage with other franchisees for ideas and support."
    # },
    # {
    #     "question": "What behaviors almost guarantee struggle?",
    #     "answer": "Minimal community visibility, Delegating everything too early, Waiting for customers instead of pursuing them, Underestimating staffing complexity, Ignoring operational KPIs, Treating it like a passive investment instead of a business."
    # },
    # {
    #     "question": "As an owner, will I be guided step-by-step if a termination or forced exit is on the table?",
    #     "answer": "Yes. The manuals and internal app give stage-by-stage guidance, checklists, and \"Process Flow\" links so FBPs and departments know exactly what to do, and in what order, during a termination or closure. That doesn't change the seriousness of termination, but it does mean the brand doesn't leave you guessing about the process."
    # },
    # {
    #     "question": "Who inside Code Ninjas is actually watching over these lifecycle events?",
    #     "answer": "Each major function has clearly defined roles in the lifecycle apps: Accounts handles damages/fees and QBO, Legal + HO manage documentation and compliance, Tech manages all software access, Marketing/Canva/Soci manage public-facing assets, and Post-Ops confirms the physical status of the location. For you as a prospect, this shows the system is process-driven, not ad hoc."
    # },
    # {
    #     "question": "What does all of this tell me about risk if I become a franchisee?",
    #     "answer": "It tells you that Code Ninjas has invested in structured, documented, and system-tracked ways to handle the hardest parts of the franchise lifecycle—resales, transfers, closures, and terminations. There are clear checklists, status tracking, and multi-team involvement rather than \"mystery\" handling, which reduces operational risk and provides a defined path even if things don't go as planned."
    # },
    # # {
    # #     "question": "What does running a successful Code Ninjas center actually require from me as an owner?",
    # #     "answer": "Success requires active leadership in the early phase, especially around: Hiring and developing a strong Center Director, Recruiting and retaining Senseis, Driving local marketing & community visibility, Monitoring KPIs weekly (retention, payroll %, student progression, leads), Maintaining quality and customer experience. Owners who treat this as a fully passive investment often struggle. Top performers remain involved at key moments even if they delegate day-to-day operations."
    # # },
    # {
    #     "question": "What are the most common reasons a center struggles or closes?",
    #     "answer": "Based on past outcomes, the most common causes are: High staff turnover (especially Center Directors), Inconsistent marketing activity, Low community engagement, Failure to review center metrics regularly, Poor financial controls during seasonal dips, Owner disengagement. Most closures occur after extended periods of slow decline—rarely overnight."
    # },
    # {
    #     "question": "How involved is Code Ninjas when operational problems arise?",
    #     "answer": "Owners receive structured support (FBP guidance, operational docs, curriculum updates, tech tickets), but day-to-day execution belongs to the owner. Support is strong, but not a replacement for active management."
    # },
    # {
    #     "question": "How long should I realistically expect it to take to reach break-even?",
    #     "answer": "Most centers reach break-even in 6–18 months, depending on: Market strength, Rent and build-out, Director quality, Parent engagement, Pre-launch marketing execution, Camp revenue performance. Centers with weak early enrollment take longer."
    # },
    # {
    #     "question": "What are real-world unexpected costs owners have experienced?",
    #     "answer": "The most frequent unexpected costs are: Additional local marketing, Staff turnover (training, recruitment, onboarding), IT equipment replacement or upgrades, Lease-related expenses, Temporary payroll spikes during growth periods. Budgeting for 10–20% more working capital than the minimum helps avoid stress."
    # },
    # {
    #     "question": "How stable is revenue over time?",
    #     "answer": "Membership revenue is stable once the center is established, but expect seasonality—especially during holidays and late summer. Camps significantly boost cash flow but require upfront planning."
    # },
    # {
    #     "question": "How difficult is it to hire and keep strong Senseis and Directors?",
    #     "answer": "Hiring is manageable but NOT passive. Senseis are often college students, which naturally creates turnover. The Center Director role is critical; strong Directors retain families, coach Senseis, maintain culture, and handle quality. A weak Director is the #1 predictor of decline."
    # },
    # {
    #     "question": "What happens operationally if my Director leaves?",
    #     "answer": "You must step in, even temporarily. Centers with owner involvement during transitions recover; absentee owners often see rapid drops in retention and service quality."
    # },
    # {
    #     "question": "What does a strong Code Ninjas territory look like?",
    #     "answer": "Successful territories typically have: Dense populations of families with school-aged kids, Healthy household income levels, Accessible retail/education corridors, Active school/PTA communities, Reasonable commercial rent. Territory strength = demographic fit and visibility."
    # },
    # {
    #     "question": "What are red flags that a territory may underperform?",
    #     "answer": "Low density or low-income population, Weak school engagement culture, High local competition in enrichment, Very high retail rent, Hard-to-access location (parking, visibility), Sparse family activity centers. Bad location decisions overshadow strong demographics."
    # },
    # {
    #     "question": "How do I evaluate whether a resale center is healthy?",
    #     "answer": "Review: Enrollment trends over the last 12–24 months, Retention and belt progression (a great quality indicator), Staff stability and Director tenure, Camp revenue and seasonal patterns, Payroll percentages, Reviews and customer sentiment online. Healthy centers show stability or growth—not erratic dips."
    # },
    # {
    #     "question": "What happens during a resale transfer behind the scenes?",
    #     "answer": "Code Ninjas coordinates a multi-department process including Legal, Finance, Tech, Marketing, Microsoft 365, Dojo, MyStudio, QBO, LineLeader, Listen360, Social Media, and Post-Ops. The SOP shows each system requires its own shutdown/reactivation sequence. (e.g., M365 offboarding, Dojo deactivation, MyStudio cancellations)"
    # },
    # {
    #     "question": "How hard is it to sell a Code Ninjas center later?",
    #     "answer": "Good centers sell much faster than underperforming ones. Buyers focus on: Enrollment stability, Clean financials, Staff consistency, Location quality, Lease terms. Saleability is primarily performance-driven."
    # },
    # {
    #     "question": "What does Code Ninjas require for a sale or partner transfer?",
    #     "answer": "You must: Notify Franchise Development, Present a buyer who meets financial/experience criteria, Ensure the center is operationally clean (systems, finances, compliance), Complete legal contracts and training, Follow the structured internal transfer workflow. This prevents messy transitions that hurt customers."
    # },
    # # {
    # #     "question": "If I choose not to renew, what does the closure process look like?",
    # #     "answer": "Code Ninjas has a highly detailed, multi-step closure SOP, covering: Legal documentation → executed & stored in SharePoint (pg. 3–4), FranConnect status updates → marking Closed/Terminated (pg. 5–6), M365 offboarding → blocking users, removing licenses, removing groups (pg. 7–9), Dojo/Website/IMPACT deactivation (pg. 10–11), MyStudio subscription cancellation & account disabling (pg. 11–12), LineLeader closure email to all families (pg. 12–13), Listen360 access removal (pg. 14), QBO deactivation (pg. 15), Marketing/Social removal across Google, FB, Yelp, Maps, etc. (pg. 16), Physical location de-identification & FF&E plan (pg. 17). This ensures centers close responsibly, with proper communication to families, clean system shutdowns, and legal compliance."
    # # },
    # {
    #     "question": "How long does a closure typically take?",
    #     "answer": "Depending on responsiveness of the owner, legal sign-off, and system deactivation, closures may take 30–90 days. The SOP shows a sequential dependency across systems and departments, meaning delays in one area slow the entire lifecycle."
    # },
    # {
    #     "question": "What leads to a franchisor-initiated termination?",
    #     "answer": "Terminations occur only when serious issues continue even after notice, such as: Chronic non-payment, Repeated refusal to follow brand standards, Legal or safety violations, Abandonment of the center."
    # },
    # {
    #     "question": "What does termination look like operationally?",
    #     "answer": "Termination initiates the exact same complex multi-system shutdown workflow as voluntary closure, but with legal oversight from the start. It includes: Immediate revocation of access, Legal documentation, System deactivation (Dojo, M365, MyStudio, QBO, LineLeader, Listen360…), Social/marketing removal, Physical location debranding. Because so many systems are integrated, termination is tightly controlled and leaves no loose ends."
    # },
    # {
    #     "question": "What early warning signs suggest my center is heading toward trouble?",
    #     "answer": "Red flags include: Declining active enrollments for 3+ consecutive months, Rapid staff turnover, High payroll-to-revenue ratio, Weak customer communication, Poor Director performance, Complaints from parents without resolution, Reduced camp attendance. Owners who intervene early usually recover; those who ignore early signals risk escalation."
    # },
    # {
    #     "question": "What has Code Ninjas improved over the years based on past failures or closures?",
    #     "answer": "Areas that have seen the most refinement include: Multi-department closure coordination (SOP confirms 10+ systems integrated), Legal communication workflows, Standardized customer communication templates, Streamlined access deactivation across platforms, FBP involvement earlier in the lifecycle of struggling centers. This evolution reflects a brand learning from experience and improving its safety nets."
    # }
]

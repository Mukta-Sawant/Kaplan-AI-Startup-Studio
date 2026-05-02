import type { SubmissionFormValues } from "./validators";

export const DEMO_SUBMISSIONS: Record<string, SubmissionFormValues> = {
  campuseats: {
    startup_name: "CampusEats",
    one_line_pitch:
      "On-demand food delivery for university campuses, powered by student couriers.",
    problem_statement:
      "Students at large universities struggle to find fast, affordable meal options outside cafeteria hours. Existing delivery apps charge high fees and often perform poorly on complex campus layouts.",
    proposed_solution:
      "A mobile app exclusively for campus food delivery. Student couriers who already know the campus handle deliveries, and restaurants get campus-specific menus with lower operating friction.",
    target_market:
      "US university students aged 18-24, starting with campuses that have 10,000+ students and dense residential housing.",
    industry_vertical: "Consumer Apps",
    business_model:
      "15% commission per order plus a $99/month restaurant partner fee.",
    traction_summary:
      "Pilot at the University of Michigan: 200 orders in the first month, 3 restaurant partners, and 12 student couriers.",
    competitive_landscape:
      "DoorDash, Uber Eats, and Grubhub serve campuses, but none are built specifically for campus-native delivery operations.",
    technical_status:
      "React Native app in beta, Firebase backend, and Stripe payment integration already working.",
    stage: "pilot",
    supporting_documents: ["https://example.com/campuseats-pilot-results.pdf"],
    team_members: [
      {
        name: "Jordan Kim",
        role: "Co-Founder & CEO",
        resume_text:
          "Junior at the University of Michigan studying Business Administration. Previously ran a campus merchandise business and understands student demand patterns and campus operations.",
        linkedin_url: "https://linkedin.com/in/jordan-kim-campuseats",
        domain_expertise:
          "Campus life, peer-to-peer commerce, student operations",
        startup_experience: "Ran a small campus merchandise business",
        commitment_level: "Full-time during summer, part-time during semester",
      },
      {
        name: "Priya Sharma",
        role: "Co-Founder & CTO",
        resume_text:
          "Senior Computer Science student with React Native and Firebase experience. Completed software internships and built mobile side projects.",
        linkedin_url: "https://linkedin.com/in/priya-sharma-campuseats",
        domain_expertise: "Mobile development, Firebase, consumer apps",
        startup_experience: "First startup",
        commitment_level: "Full-time during summer, part-time during semester",
      },
    ],
  },
  researchlink: {
    startup_name: "ResearchLink",
    one_line_pitch:
      "AI-powered platform connecting academic researchers with industry R&D teams.",
    problem_statement:
      "Independent academic researchers struggle to commercialize their findings, while industry R&D teams lack visibility into early-stage academic work before it becomes widely known.",
    proposed_solution:
      "A matchmaking platform that uses NLP to analyze research papers and match them with relevant corporate R&D departments, enabling early licensing and collaboration conversations.",
    target_market:
      "Life sciences, materials science, and deep-tech researchers at US and EU universities, along with enterprise R&D teams seeking early access to innovation.",
    industry_vertical: "DeepTech / Advanced Materials",
    business_model:
      "SaaS subscription for corporate R&D teams at $500/month per seat, plus university platform fees for researcher access.",
    traction_summary: "",
    competitive_landscape:
      "ResearchGate and Academia.edu focus on discovery and paper sharing, not early-stage licensing or industry matchmaking.",
    technical_status:
      "Proof-of-concept NLP pipeline built in Python. No production infrastructure yet.",
    stage: "prototype",
    supporting_documents: [],
    team_members: [
      {
        name: "Dr. Maya Osei",
        role: "Founder & CEO",
        resume_text:
          "PhD in Computational Biology from MIT with 8 years of academic research experience and 14 peer-reviewed publications. Building ResearchLink solo while remaining active in academia.",
        linkedin_url: "https://linkedin.com/in/maya-osei-researchlink",
        domain_expertise:
          "Computational biology, NLP, academic publishing, research workflows",
        startup_experience: "None",
        commitment_level:
          "Part-time at 20 hours/week while maintaining academic role",
      },
    ],
  },
  neuropatch: {
    startup_name: "NeuroPatch",
    one_line_pitch:
      "Non-invasive EEG-based cognitive monitoring patch for early Alzheimer's detection in primary care.",
    problem_statement:
      "Alzheimer's disease is often diagnosed years after neurological changes begin, and primary care physicians lack accessible, low-cost tools for early screening.",
    proposed_solution:
      "A wearable EEG patch used during routine GP visits. A proprietary signal-processing algorithm identifies early-stage biomarkers associated with cognitive decline and integrates with EHR systems through FHIR.",
    target_market:
      "Primary care physicians in the US and UK, with expansion into neurology clinics and memory-care centers.",
    industry_vertical: "HealthTech / MedTech",
    business_model:
      "Device lease model at $200/month per practice including device, disposable patches, and software platform.",
    traction_summary:
      "NHS pilot with 3 GP practices in Manchester, 47 patient assessments, 91% clinician satisfaction, and an NIH SBIR Phase I award of $250,000.",
    competitive_landscape:
      "Closest alternatives are specialist neuroimaging and blood biomarker tests. No major EEG-based screening device is broadly deployed in GP settings.",
    technical_status:
      "CE Mark application submitted, FDA Breakthrough Device Designation application in progress, and algorithm validated on a 340-patient dataset.",
    stage: "pilot",
    supporting_documents: [
      "https://example.com/neuropatch-clinical-validation.pdf",
    ],
    team_members: [
      {
        name: "Dr. Sarah Whitfield",
        role: "Co-Founder & CEO",
        resume_text:
          "MD and PhD in Neuroscience from UCL with 12 years in neurology research. Previously commercialized a medical device licensed to Medtronic.",
        linkedin_url: "https://linkedin.com/in/sarah-whitfield-neuropatch",
        domain_expertise:
          "Neurology, clinical trials, medical device commercialization",
        startup_experience: "One prior device licensing deal",
        commitment_level: "Full-time",
      },
      {
        name: "Amir Hassan",
        role: "Co-Founder & CTO",
        resume_text:
          "Biomedical engineer with 8 years at Philips Healthcare focused on EEG signal processing, medical firmware, and regulatory compliance.",
        linkedin_url: "https://linkedin.com/in/amir-hassan-neuropatch",
        domain_expertise:
          "EEG signal processing, medical device firmware, CE and FDA compliance",
        startup_experience: "First startup, deep industry experience",
        commitment_level: "Full-time",
      },
      {
        name: "Dr. Priya Nair",
        role: "Chief Medical Officer",
        resume_text:
          "GP Principal with 15 years in primary care and NHS digital health advisory experience. Leading NeuroPatch clinical validation and adoption strategy.",
        linkedin_url: "https://linkedin.com/in/priya-nair-neuropatch",
        domain_expertise:
          "Primary care, NHS procurement, clinical validation",
        startup_experience: "None",
        commitment_level: "Part-time, 2 days/week",
      },
    ],
  },
};

export const DEMO_SUBMISSION_OPTIONS = [
  { value: "campuseats", label: "CampusEats Demo" },
  { value: "researchlink", label: "ResearchLink Demo" },
  { value: "neuropatch", label: "NeuroPatch Demo" },
] as const;

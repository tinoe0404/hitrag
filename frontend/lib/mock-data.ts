import { AccessTier } from "@/components/ui/citation-tag";
import { GroundingState } from "@/components/ui/grounding-rule";
import { CitationDetail } from "@/components/chat/citation-drawer";
import { UserProfile } from "@/components/chat/chat-sidebar";

export interface MockMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  groundingState?: GroundingState;
  timestamp: string;
  citations?: Record<number, CitationDetail>;
  restrictedData?: {
    requiredTier: string;
    targetOffice: string;
    officeContact: string;
  };
}

export interface MockConversation {
  id: string;
  title: string;
  timestamp: string;
  group: "Today" | "Earlier this week";
  messages: MockMessage[];
}

export const MOCK_USER_PROFILES: Record<AccessTier, UserProfile> = {
  Student: {
    name: "Tendai M.",
    role: "Student",
    department: "Software Engineering",
    title: "Year 2",
  },
  Lecturer: {
    name: "Dr. Chikuse",
    role: "Lecturer",
    department: "Computer Science",
    title: "Senior Lecturer",
  },
  Admin: {
    name: "Prof. N. Moyo",
    role: "Admin",
    department: "Academic Affairs & Registrar",
    title: "Deputy Registrar",
  },
  Public: {
    name: "Guest Visitor",
    role: "Public",
    department: "General Information",
    title: "Public Guest",
  },
};

export const MOCK_CONVERSATIONS: MockConversation[] = [
  {
    id: "conv-101",
    title: "Software Eng Attachment Requirements",
    timestamp: "10:14 AM",
    group: "Today",
    messages: [
      {
        id: "m-101-1",
        role: "user",
        content: "What are the requirements for industrial attachment as a 2nd year Software Engineering student?",
        timestamp: "10:14 AM",
      },
      {
        id: "m-101-2",
        role: "assistant",
        groundingState: "grounded",
        timestamp: "10:14 AM",
        content: "According to official HIT academic handbooks, Part II (2nd year) Software Engineering students preparing for industrial attachment must satisfy the following criteria:\n\n• Clear and pass all Part II core modules including Software Design (SE2101) and Data Structures (CS2102) without pending module carry-overs [1].\n\n• Secure placement for a minimum continuous duration of 30 weeks within an approved ICT or software development industry organization [2].\n\n• Maintain a cumulative GPA of 2.0 or higher prior to official departmental attachment deployment [3].",
        citations: {
          1: {
            index: 1,
            documentTitle: "HIT Industrial Attachment Regulations, 2026",
            department: "Software Engineering",
            documentType: "Academic Regulation",
            lastUpdated: "12 Jan 2026",
            accessTier: "Student",
            excerpt: "All Part II Software Engineering students proceeding to Part III Industrial Attachment must successfully clear all prerequisite modules (SE2101 Software Design and CS2102 Data Structures) with no carry-over modules.",
            documentUrl: "#",
          },
          2: {
            index: 2,
            documentTitle: "HIT General Academic Regulations & Standards",
            department: "Academic Affairs",
            documentType: "Policy Handbook",
            lastUpdated: "04 Feb 2026",
            accessTier: "Public",
            excerpt: "Industrial attachment placement must span a minimum continuous period of 30 weeks in an approved industrial setting under joint academic and workplace supervision.",
            documentUrl: "#",
          },
          3: {
            index: 3,
            documentTitle: "HIT Examination and Assessment Code of Conduct",
            department: "Examinations Committee",
            documentType: "Institutional Policy",
            lastUpdated: "18 Nov 2025",
            accessTier: "Student",
            excerpt: "Candidates must maintain a minimum cumulative grade point average (CGPA) of 2.0 or higher prior to attachment deployment approval.",
            documentUrl: "#",
          },
        },
      },
    ],
  },
  {
    id: "conv-102",
    title: "Registration & Module Carry Over Deadline",
    timestamp: "Yesterday",
    group: "Earlier this week",
    messages: [
      {
        id: "m-102-1",
        role: "user",
        content: "When does semester registration close for Part II students?",
        timestamp: "09:30 AM",
      },
      {
        id: "m-102-2",
        role: "assistant",
        groundingState: "grounded",
        timestamp: "09:31 AM",
        content: "Semester registration for Part II undergraduate students closes strictly at 17:00 HRS on Friday of Week 3 of the academic semester [1]. Late registration incurs a non-refundable administrative surcharge and requires Chairperson clearance [2].",
        citations: {
          1: {
            index: 1,
            documentTitle: "HIT General Academic Calendar & Enrollment Dates 2026",
            department: "Academic Registrar",
            documentType: "University Calendar",
            lastUpdated: "05 Jan 2026",
            accessTier: "Public",
            excerpt: "Normal semester enrollment and course registration closes on Friday of Week 3 at 17:00 HRS for all Part II and Part IV returning students.",
            documentUrl: "#",
          },
          2: {
            index: 2,
            documentTitle: "HIT Bursar Fee Schedule & Penalty Policy",
            department: "Bursary",
            documentType: "Fee Structure",
            lastUpdated: "10 Jan 2026",
            accessTier: "Student",
            excerpt: "Any registration completed during Week 4 incurs a late penalty fee of $50 USD. No registrations are permitted after Week 4.",
            documentUrl: "#",
          },
        },
      },
    ],
  },
  {
    id: "conv-103",
    title: "Staff HR Salary & Appraisal Benchmarks",
    timestamp: "Aug 10",
    group: "Earlier this week",
    messages: [
      {
        id: "m-103-1",
        role: "user",
        content: "What are the internal salary scale benchmarks and staff appraisal policies for 2026?",
        timestamp: "02:15 PM",
      },
      {
        id: "m-103-2",
        role: "assistant",
        groundingState: "restricted",
        timestamp: "02:15 PM",
        content: "RESTRICTED_ACCESS",
        restrictedData: {
          requiredTier: "Staff / Admin",
          targetOffice: "HIT Human Resources & Staff Relations Office",
          officeContact: "hr-enquiries@hit.ac.zw",
        },
      },
    ],
  },
];

# coding: utf-8
{
    'name': "HRMS Recruitment",

    'summary': """
        Part of HRMS V3 Application""",

    'description': """
        This application tackles the recruitment/job requisition side of HR/Recruitment
        Its main components are: Personnel Requisition, Job Posting, Candidate Sourcing, Candidate
        Assessment, Shortlist and Job Offer, and Induction.
    """,

    'author': "John Ardosa, Raymund Martinez, and Ralf Cabarogias - Agilis Enterprise Solutions",
    'website': "http://www.yourcompany.com",

    'category': 'HR',
    'version': '0.1',

    'depends': [
        'base',
        'contacts',
        'hr',
        'hr_contract',
        'hr_recruitment'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/personnel_requisition.xml',
        'views/job_posting.xml',
        'views/skills.xml',
        'views/candidate_sourcing.xml',
        'views/candidate_assessment.xml',
        'wizard/applicant.xml',
        'data/sequence.xml',
    ],
}

import os

from habutax.form import Form, Jurisdiction
from habutax.inputs import *
from habutax.fields import *
from habutax.pdf_fields import *
import habutax.enum as enum


class Form1040SC(Form):
    form_name = "1040_sc"
    tax_year = 2023
    description = "Schedule C (Form 1040)"
    long_description = "Profit or Loss from Business (Sole Proprietorship)"
    jurisdiction = Jurisdiction.US
    sequence_no = 9

    def __init__(self, **kwargs):
        NUM_FIELDS = 14
        inputs = [
            StringInput('proprietor_name', description="Enter the full name of the proprietor."),
            EnumInput('ssn_source', enum=enum.taxpayer_spouse_or_estate_trust, description="Is the proprietor you, your spouse, or an estate or trust?"),
            StringInput('a', description="Describe the business or professional activity that provided your principal source of income reported on line 1. Give the general field or activity and the type of product or service. If your general field or activity is wholesale or retail trade, or services connected with production services (mining, construction, or manufacturing), also give the type of customer or client; for example, “wholesale sale of hardware to retailers” or “appraisal of real estate for lending institutions.”"),
            NaicsInput('b', description="Enter the six-digit code from the Principal Business or Professional Activity Codes chart."),
            StringInput('c', description="Business name. If no separate business name, leave blank."),
            StringInput('d', description="If you were issued a Form SS-4, enter the EIN from that form. If you are the sole owner of an LLC that is not treated as a separate entity for federal income tax purposes, enter on line D the EIN that was issued to the LLC (in the LLC's legal name) for a qualified retirement plan, to file employment, excise, alcohol, tobacco, or firearms returns, or as a payer of gambling winnings. If you do not have such an EIN, leave line D blank."),
            StringInput('e1', description="Business address line one (including suite or room no.) "),
            StringInput('e2', description="Business address line two: City, town or post office, state, and ZIP code"),
            EnumInput('f', enum=enum.business_accounting_method, description="Accounting method"),
            StringInput('f_other', description="Specify the 'other' accounting method as permitted by the Internal Revenue Code"),
            BooleanInput('accounting_method_changed', description="Are you using a different accounting method for this business compared to the same business in the previous tax year?"),
            BooleanInput('g', description=f"Did you 'materially participate' in the operation of this business during {self.tax_year}?"),
            BooleanInput('h', description=f"Did you start this business in {self.tax_year}?"),
            BooleanInput('i', description="Did you make any payments in 2023 that would require you to file Form(s) 1099? See instructions for Schedule C"),

        ]

        optional_fields = [
        ]

        def ssn(self, i, v):
            if i["ssn_source"] == enum.taxpayer_spouse_or_estate_trust.taxpayer:
                return v["1040.you_ssn"]
            if i["ssn_source"] == enum.taxpayer_spouse_or_estate_trust.spouse:
                return v["1040.spouse_ssn"]
            return self.not_implemented(detailed="Businesses owned by Estates and Trusts are not implemented.")

        def f(self, i, v):
            if i['accounting_method_changed']:
                return self.not_implemented(detailed="To change your accounting method, you must generally file Form 3115, which is not implemented.")
            return i['f']

        required_fields = [
            StringField('proprietor_name', lambda s, i, v: i['proprietor_name']),
            StringField('ssn', ssn),
            StringField('a', lambda s, i, v: i['a']),
            StringField('b', lambda s, i, v: i['b']),
            StringField('c', lambda s, i, v: i['c']),
            StringField('d', lambda s, i, v: i['d']),
            StringField('e1', lambda s, i, v: i['e1']),
            StringField('e2', lambda s, i, v: i['e2']),
            EnumField('f', enum=enum.business_accounting_method, value_fn=f),
            StringField('f_other', lambda s, i, v: i['f_other'] if i['f'] == enum.business_accounting_method.other else ""),
            BooleanField('g', lambda s, i, v: i['g'] if i['g'] else s.not_implemented(detailed="Filers that did not 'materially participate' in the operation of this business during the tax year are not implemented.")),
        ]

        for line in range(NUM_FIELDS):
            int_payer = StringField(f'1_payer_{line}', lambda s, i, v: v[f'1099-int:{s.which_1099int}.payer'] if s.which_1099int < i['1040.number_1099-int'] else None)
            int_payer.which_1099int = line
            int_amount = FloatField(f'1_amount_{line}', lambda s, i, v: v[f'1099-int:{s.which_1099int}.box_1'] + v[f'1099-int:{s.which_1099int}.box_3'] if s.which_1099int < i['1040.number_1099-int'] else None)
            int_amount.which_1099int = line
            div_payer = StringField(f'5_payer_{line}', lambda s, i, v: v[f'1099-div:{s.which_1099div}.payer'] if s.which_1099div < i['1040.number_1099-div'] else None)
            div_payer.which_1099div = line
            div_amount = FloatField(f'5_amount_{line}', lambda s, i, v: v[f'1099-div:{s.which_1099div}.box_1a'] if s.which_1099div < i['1040.number_1099-div'] else None)
            div_amount.which_1099div = line

            required_fields += [int_payer, int_amount, div_payer, div_amount]

        pdf_fields = [
            TextPDFField('topmostSubform[0].Page1[0].f1_01[0]', '1040.full_names'),
            TextPDFField('topmostSubform[0].Page1[0].f1_02[0]', '1040.you_ssn', max_length=11),
            TextPDFField('topmostSubform[0].Page1[0].Line1_ReadOrder[0].f1_03[0]', '1_payer_0'),
            TextPDFField('topmostSubform[0].Page1[0].f1_04[0]', '1_amount_0'),
            # Remaining input fields for field 1 are below in a 'for' loop
            TextPDFField('topmostSubform[0].Page1[0].f1_31[0]', '2'),
            TextPDFField('topmostSubform[0].Page1[0].f1_32[0]', '3'),
            TextPDFField('topmostSubform[0].Page1[0].f1_33[0]', '4'),
            TextPDFField('topmostSubform[0].Page1[0].ReadOrderControl[0].f1_34[0]', '5_payer_0'),
            TextPDFField('topmostSubform[0].Page1[0].f1_35[0]', '5_amount_0'),
            # Remaining input fields for field 5 are below in a 'for' loop
            TextPDFField('topmostSubform[0].Page1[0].f1_64[0]', '6'),
            ButtonPDFField('topmostSubform[0].Page1[0].c1_1[0]', '7a', '1'),
            ButtonPDFField('topmostSubform[0].Page1[0].c1_1[1]', '7a', '2', lambda s, v, f: not v),
            ButtonPDFField('topmostSubform[0].Page1[0].c1_2[0]', '7b', '1'),
            ButtonPDFField('topmostSubform[0].Page1[0].c1_2[1]', '7b', '2', lambda s, v, f: not v),
            TextPDFField('topmostSubform[0].Page1[0].f1_65[0]', '7b_country'),
#            TextPDFField('topmostSubform[0].Page1[0].f1_66[0]', '7b_country'),
            ButtonPDFField('topmostSubform[0].Page1[0].c1_3[0]', '8', '1'),
            ButtonPDFField('topmostSubform[0].Page1[0].c1_3[1]', '8', '2', lambda s, v, f: not v),
        ]

        # The first of each of the fields in this loop is handled above,
        # because they require different "selectors"
        for line in range(1, NUM_FIELDS):
            one_payer = TextPDFField(f'topmostSubform[0].Page1[0].f1_{3+line*2:02d}[0]', f'1_payer_{line}')
            one_amt = TextPDFField(f'topmostSubform[0].Page1[0].f1_{4+line*2:02d}[0]', f'1_amount_{line}')
            five_payer = TextPDFField(f'topmostSubform[0].Page1[0].f1_{34+line*2:02d}[0]', f'5_payer_{line}')
            five_amt = TextPDFField(f'topmostSubform[0].Page1[0].f1_{35+line*2:02d}[0]', f'5_amount_{line}')
            pdf_fields += [one_payer, one_amt, five_payer, five_amt]

        pdf_file = os.path.join(os.path.dirname(__file__), 'f1040sb.pdf')
        super().__init__(__class__, inputs, required_fields, optional_fields, pdf_fields=pdf_fields, pdf_file=pdf_file, **kwargs)

    def needs_filing(self, values):
        return True

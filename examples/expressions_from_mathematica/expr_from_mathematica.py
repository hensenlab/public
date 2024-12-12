# -*- coding: utf-8 -*-
"""
Created 2022

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.
"""

import re


"""
Right click on selected expression in Mathematica and click copy as, Plain text
"""
expr = r'{-((mu0 Rsphere^3 (-3 x (My y+Mz z)+Mx (-2 x^2+y^2+z^2)))/(3 (x^2+y^2+z^2)^(5/2))),-((mu0 Rsphere^3 (-3 y (Mx x+Mz z)+My (x^2-2 y^2+z^2)))/(3 (x^2+y^2+z^2)^(5/2))),-((mu0 Rsphere^3 (-3 (Mx x+My y) z+Mz (x^2+y^2-2 z^2)))/(3 (x^2+y^2+z^2)^(5/2)))}'

escaped_characters = set(re.findall(r'\\\[\w*\]',expr))
for k in escaped_characters:
    expr = expr.replace(k, k[2:-1])

literal_replace_dict = {
    'EllipticPi[' : 'ellipp(',
    'Pi':'np.pi',
    '^':'**',
    ' + '  : '+',
    ' - '  : '-',
    ' -> ' : '=', 
    ' = '  : '=',
    'Abs[' : 'np.abs(',
    'Log[' : 'np.log(' ,
    'Exp[' : 'np.exp(' ,
    'Sqrt[': 'np.sqrt(' ,
    'Sin[' : 'np.sin(' ,
    'Tan[' : 'np.tan(' ,
    'Cos[' : 'np.cos(' ,
    'Sec[' : '1/np.cos(',
    'EllipticE[' : 'scipy.special.ellipe(',
    'EllipticK[' : 'scipy.special.ellipk(',
    ']'    : ')',
    ' ' : '*',
    ')(' : ')*(',
    }

for k,v in literal_replace_dict.items():
    expr = expr.replace(k, v)

print(expr)
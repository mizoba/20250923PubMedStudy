import re
def replace(text):
    text=text.replace(',', '.').replace('•', '.').replace('x', 'e').replace('×', 'e').replace(' ','').replace('(','').replace(')','')
    text=text.replace('exp','e').replace('Exp','e').replace('E','e')
    # Remove ALL whitespace (including thin space \u2009)
    # \s matches [ \t\n\r\f\v] and unicode whitespace characters
    text = re.sub(r'\s+', '', text)
    return text

def text_to_pval_and_oper(text):
    """
    Extracts P values and their operators from text based on specific 
    regex and homogenization rules.
    
    Args:
        text (str): The abstract or text to analyze.
        
    Returns:
        list of tuples: A list of (operator, p_value_float).
    """
    
    # 1. THE SEARCH STRING
    # This is the regex pattern provided in the text, adapted for Python.
    # We use named groups (?P<name>...) to easily retrieve specific parts later.
    # Group 'op': Captures the operator/sign
    # Group 'num': Captures the number part (including sci notation/percentage suffix)
    
    p_value_pattern = r"""(?x)              # Verbose mode (ignore whitespace in regex)
        (\s|\()                             # Preceding space or parenthesis
        [Pp]{1}                             # 'P' or 'p'
        (\s|-)* # Optional space or hyphen
        (value|values)?                     # Optional 'value' word
        (\s)* # Optional space
        (?P<op>                             # START GROUP: Operator
           ([=<>≤≥]|less\s+than|of\s+<)+    # Matches signs, 'less than', 'of <'S$
        )                                   # END GROUP: Operator
        (\s)* # Optional space
        (?P<num>                            # START GROUP: Number/Value
            (?P<digits>([0-9]|([\,\.•][0-9]))        # First digit or separator+digit
            [0-9]* # Following digits
            [\,\.•]?                      # Optional separator
            [0-9]*) # Decimal digits
            (\s)* # Space before suffix
            (                               # Suffix group (percentage or sci notation)
                (\%)|                       # Percentage sign
                ([x×]?(\s)*(?P<base>[0-9]*)(\s)*((exp|Exp|E|e)?(\s)*(?P<exponent>((\((\s)*(-){1}(\s)*[0-9]+(\s)*\))|((\s)*(-){1}(\s)*[0-9]+))))?)
            )
        )                                   # END GROUP: Number
    """
    
    results = []
    
    # Iterate over all matches in the text
    for match in re.finditer(p_value_pattern, text):
        operator_str = match.group('op').strip()
        raw_value_str = match.group('num').strip()
        digits=match.group('digits').strip()
        base=match.group('base')
        exponent=match.group('exponent')        
        
        
        digits=replace(digits)
        raw_value_str=replace(raw_value_str)
        operator_str = replace(operator_str)
        if base:
            base=base.strip()
            base=replace(base)
        if exponent:
            exponent=exponent.strip()
            exponent=replace(exponent)
        
        # 2. HOMOGENIZATION & PARSING
        
        # remove wrong forms
        # Rule: Discard '.int' format (typos like 0012 without decimal points)
        
        if raw_value_str.count('.') > 1:
            continue
        else:
            digits=float(digits)
        
        # Rule: consider % format
        if '%' in raw_value_str:
            p_value = digits*0.01
        # has extra exponent term, with base and exponent
        elif 'e' in raw_value_str:
            if base and not float(base)==0:
                base=float(base)
            else:
                base=10 #According to previous study from jama, We assume base is 10
            if exponent:
                exponent=float(exponent)
            else:
                exponent=1 # If exponent is missing, we let exponent as 1, excluding the effect of the exponent.
            p_value=digits*(base**exponent)
        else:
            p_value=digits
            
        # Rule: Discard if not in interval (0, 1]
        if p_value <= 0 or p_value >= 1:
            continue
        
        # Classify operators
        operator_str=operator_str.replace('of','').replace('≤','<').replace('≥','>').replace('lessthan','<')
        if '=' in operator_str:
            operator='='
        if '>' in operator_str:
            operator='>'
        if '<' in operator_str:
            operator='<'
        if '>' in operator_str:
            if '<' in operator_str:
                operator='ambiguous'
        results.append((p_value,operator))

    return results

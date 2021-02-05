import re


def remove_comments(code):
    """
    Removes Lua comments through the string, given to this function.
    Then removes empty strings (which also appear after removing comments);
    as a side effect, all tabulations are also removed.

    @param code: string, containing sourcecode which should be processed.
    @return: string withe sourcecode without any comments and tabulations
    """
    no_comments_code = re.sub(r"--\[\[[\s\S]*\]\]|"          # multi-line comments like --[[ comment ]]
                              r"--\[=\[[\s\S]*\]=\]|"        # multi-line comments like --[=[ comment ]=]
                              "--.*",                       # single-line comments like -- comment
                              "", code)
    cleaned_code = re.sub(r"^\s*", "", no_comments_code, flags=re.MULTILINE)

    return cleaned_code


def check_if_data_function(code):
    """
    Checks if the function is believed to be a data function, meaning it is used only for storing
    information, but not any calculations.
    For now, data function is the function, which consists only of `return {data` statement.
    (there's not always an ending bracket; it might be a bug, but semantically they still contain data).

    @param code: sourcecode of the function (with no comments)
    @return: True/False
    """
    if re.match(r"^return {[\s\S]*$", code):
        return True
    else:
        return False

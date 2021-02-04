import re


def remove_comments(code):
    """
    Removes Lua comments through the string, given to this function.
    Then removes empty strings (which also appear after removing comments);
    as a side effect, all tabulations are also removed.
    @param code: string, containing sourcecode which should be processed.
    @return: string withe sourcecode without any comments and tabulations
    """
    no_comments_code = re.sub("--\[\[[\s\S]*\]\]|"          # multi-line comments like --[[ comment ]]
                              "--\[=\[[\s\S]*\]=\]|"        # multi-line comments like --[=[ comment ]=]
                              "--.*",                       # single-line comments like -- comment
                              "", code)
    cleaned_code = re.sub("^\s*", "", no_comments_code, flags=re.MULTILINE)

    return cleaned_code

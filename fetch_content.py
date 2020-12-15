## imports
import sys

## define constants
MIN_IDX = 0
MAX_IDX = 8

def get_text(wiki):
    print(wiki)

if __name__ == "__main__":
    
    ## Check arguments for errors
    if len(sys.argv)<3:
        print("Error: Two args required: start and end index. E.g python3 fetch_content.py 1 8.")
        sys.exit()
    
    try:
        start_idx = int(sys.argv[1])
        end_idx = int(sys.argv[2])
    except:
        print("Error: Both indices should be integer from 0 to 8.")
        sys.exit()
    
    if start_idx<MIN_IDX or end_idx<MIN_IDX or start_idx>MAX_IDX or end_idx>MAX_IDX:
        print("Error: Both indices should be in the range 0 to 8.")
        sys.exit()

    if start_idx>end_idx:
        print("Error: ending index must be greater than start index.")
        sys.exit()
    

    ## List the wikis in the rage [start_idx, end_idx] and run function
    with open('wikipages.txt') as file:
        for i, line in enumerate(file):
            if i>=start_idx:
                wiki = line.strip(' \n')
                get_text(wiki)
            if i==end_idx:
                break
    
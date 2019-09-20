# To iterate files in input directory
import sys
import os
import numpy as np
import pandas as pd
import re

# Take fixed width as command line argument from user
f_width=int(sys.argv[1])

# Define input and output directories. Host directories are mounted in the docker container
ipDir = '/var/input/'
opDir = '/var/output/'

# Read the specification file
with open('./spec.json') as f:
        lines = f.read()

# Remove newlines
lines = lines.replace("\n", "")

# Extract column names and widths
# Considering the fact that they are contained in lists with the first being ColumnNames and second being Offsets
cols = lines.split('[')[1].split(']')[0].replace(" ", "")
offsets = lines.split('[')[2].split(']')[0].replace(" ", "")

# OR this can be extracted as below. This is a bit more flexible since ordering is not important for column names and offsets.

# Split based on "ColumnNames", extract the 1st value, split is again on ] since the values are contained in a list. Split again on the [ and extract the
# first value. Remove extra spaces and quotes
cols=lines.split("ColumnNames",1)[1].split(']')[0].split('[')[1].replace(" ", "").replace("\"", "")

# Convert cols into a list
headers=list(cols.split(','))

# Split based on Offsets and extract the first value. Then split on closing ] to extract the entire block, split on opening [ and get the first value.
# Remove extra spaces and quotes
offsets = lines.split("Offsets",1)[1].split(']')[0].split('[')[1].replace(" ", "").replace("\"", "")

# Split based on FixedWidthEncoding and extract the first value. Then split on , to get the block and finally on :
f_width_enc = lines.split("FixedWidthEncoding",1)[1].split(',')[0].split(':')[1].lstrip()

# Extract IncludeHeader in a similar way as above
inc_header = lines.split("IncludeHeader",1)[1].split(',')[0].split(':')[1].lstrip()

# Extract DelimitedEncoding in a similar way
dem_enc = lines.split("DelimitedEncoding",1)[1].split('}')[0].replace("\":", "").lstrip()

# Same logic as above
# Convert offsets into list of ints
widths=list(map(int,(offsets.split(','))))

# Same logic for below.
input_enc=lines.split("FixedWidthEncoding",1)[1].split(',')[0].split(':')[1].replace(" ", "")
inc_header = lines.split("IncludeHeader",1)[1].split(',')[0].split(':')[1].replace(" ", "")
delimited_enc = lines.split("DelimitedEncoding",1)[1].split(',')[0].split(':')[1].replace(" ", "").strip("}")

# Definition of fixed_width generator function
# This function takes the input params and generates a fixed width file. Fixed width is set by the user
# and given as an argument. The file content will be shown in columns, each of size=fixed_width. Each
# column will be separated by offset width dtores in widths list.

# Input params :
# @@ input_file : This is the name of the input file to be read
# @@ encoding : This is the enconding of out fixed width file


tmp2=''
tmp=''
max_len = (f_width*10)+sum(widths)
# Fixed width generator function
def fixed_width_generator(input_file):
        # Get the filename
        op_file = input_file.split('/')[-1].split('.')[0]

        # Read the input file
        with open(input_file, encoding='cp1252') as file:
                try:
                        lines = file.read()
                except:
                        print("Codec error : Can't be converted into windows-1252 encoding.")
                        return

        # Declare the output file pointer. Set the encoding as cp1252 stored in f_width_enc(spec file)
        fwp = open(opDir + op_file+'_fixed_width.txt', 'w+', encoding='cp1252')

        # Remove newlines and spaces from lines
        lines = lines.replace("\n", "").replace(" ", "")

        block=''
        file_content = lines
        
	# Create the header block
        header_block = ''
        for i in range(len(headers)):
                header_block = header_block + headers[i]+(" "*(widths[i]+(f_width-len(headers[i]))))

	# File block parsing
        i=0
        cnt=0
        block=''
        is_cp1252=0
        txt_str=file_content
        line_count = 0
	# Iterate file content
        while(txt_str):   
	    # This is to generate 10 colummns
            for k in range(len(widths)):
                y = len(txt_str)
                cnt=0
                tmp=''
                j=0
		# form one block of f_width chars max as we f_width
                while (cnt<f_width and j<=y-1): 
                    size=0
                    # check for unicode chars
                    myResult1 = re.findall(u"[^\u0000-\u007e]+", txt_str[j])
		    # Yes, it is unicode
                    if ( len(myResult1) > 0):
			# since unicode characters take 2 bytes, increment by 2
                        cnt=cnt+2 
                    else:
                        cnt=cnt+1
                   
		    # cnt will be 6 when the three characters read are all unicode
		    # in that case, we will have to not condider the last one and 
		    # append apce instead 
                    if(cnt!=6 ):
			# Add non-unicode character
                        tmp=tmp + txt_str[j]
			# calculate size to update text_str
                        size=len(tmp)
                        j=j+1
                    elif (cnt == 6 ) :
			# all unicode
                        size=len(tmp)
			# decrement counter to not skip character
                        j=j-1
               
		# add spaces if length less than f_width 
                tmp = tmp + " "*(f_width-size)
                # Update file_content
                txt_str = txt_str[size:]
                block=block+(tmp)
		# add offset
                block=block+(" "*widths[k])
                k=k+1
                
            # add newline
            block=block+'\n'
         
        # Write the block to the output file 
        total = header_block + '\n' + block
        fwp.write(total)
        fwp.close()
        
# Iterate each in ipDir
for filename in os.listdir(ipDir):
	if not(filename.startswith('.')):
        	fixed_width_generator(ipDir + filename)

def generate_csv(input_file):
        # Take out the base filename
        basefile = input_file.split('/')[-1].split('.')[0]
        with open(input_file, encoding='cp1252') as f:
                # Create a dataframe having columns as headers
                df = pd.DataFrame(columns=[headers])
                # Read the first line, this will be of headers, skip it
                line = f.readline()
                i = 0
                # Loop to read entire file
                while(line):
                        tmp=[]
                        # Read the next line
                        line = f.readline()
                        # Replace spaced with commas
                        value = " ".join(str(line).split()).replace(" ", ",")
                        # Split to get the values
                        val = value.split(',')
                        # Conditions to handle missing values
                        # If the length is same as the no of columns, put the value straight
                        if ( len(val) == len(headers)):
                                df.loc[i] = val
                        elif (len(val)==1 and val[0]==''):   # no further value case
                                continue
                        elif (len(val)<len(headers)):
                                # Case when length is less than headers
                                # Append NA at the remaning elements
                                # Extract till the last value
                                df.loc[i,:len(val)]=val
                                # Put NaN for remaining
                                df.loc[i, len(val):]=np.NaN

                        # Increment counter
                        i=i+1

                # Replace NaN with blanks, this depends upon use case
                df = df.replace(np.nan, '', regex=True)

        #Save to CSV with encoding as utf-8 stored in dem_enc(spec.json file)
        df.to_csv(opDir+basefile+'.csv', encoding=dem_enc, header=True, index=False)

#Iterate through all the files
for filename in os.listdir(opDir):
	# Ignore hidden files
	if not(filename.startswith('.')):
		generate_csv(opDir + filename)

# To iterate files in input directory
import sys
import os
import numpy as np
import pandas as pd

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
#print(offsets)

# Split based on FixedWidthEncoding and extract the first value. Then split on , to get the block and finally on :
f_width_enc = lines.split("FixedWidthEncoding",1)[1].split(',')[0].split(':')[1].lstrip()
#print(f_width_enc+'\n')

# Extract IncludeHeader in a similar way as above
inc_header = lines.split("IncludeHeader",1)[1].split(',')[0].split(':')[1].lstrip()
#print(inc_header+'\n')

# Extract DelimitedEncoding in a similar way
dem_enc = lines.split("DelimitedEncoding",1)[1].split('}')[0].replace("\":", "").lstrip()
#print(dem_enc+'\n')

# Same logic as above
# Convert offsets into list of ints
widths=list(map(int,(offsets.split(','))))

# Same logic for below.
input_enc=lines.split("FixedWidthEncoding",1)[1].split(',')[0].split(':')[1].replace(" ", "")
inc_header = lines.split("IncludeHeader",1)[1].split(',')[0].split(':')[1].replace(" ", "")
delimited_enc = lines.split("DelimitedEncoding",1)[1].split(',')[0].split(':')[1].replace(" ", "").strip("}")

# Test with a sample file having below content, stored locally on my machine
#10012345678ABCDEF123abc
#11012345678ABC12345abcd
#12012345678111111abcdef
#10012345678AABCDEF123abc
#11012345678AABC12345abcd
#12012345678A111111abcdef

# Max length of one line in the output file
max_len = (f_width*10)+sum(widths)
#max_len

# Definition of fixed_width generator function
# This function takes the input params and generates a fixed width file. Fixed width is set by the user
# and given as an argument. The file content will be shown in columns, each of size=fixed_width. Each
# column will be separated by offset width dtores in widths list.

# Input params :
# @@ input_file : This is the name of the input file to be read
# @@ encoding : This is the enconding of out fixed width file

# Set the encoding as windows-1252
def fixed_width_generator(input_file):
        # Get the filename
        op_file = input_file.split('/')[-1].split('.')[0]

        # Read the input file
        with open(input_file, encoding=f_width_enc) as file:
                try:
                        lines = file.read()
                except:
                        print("Codec error : Can't be converted into windows-1252 encoding.")
                        return

        # Declare the output file pointer. Set the encoding as cp1252 stored in f_width_enc(spec file)
        fwp = open(opDir + op_file+'_fixed_width.txt', 'w+', encoding=f_width_enc)

        # Remove newlines and spaces from lines
        lines = lines.replace("\n", "").replace(" ", "")

        block=''
        file_content = lines

        # Create the header block
        header_block = ''
        for i in range(len(headers)):
                header_block = header_block + headers[i]+(" "*(widths[i]+(f_width-len(headers[i]))))

        # Loop till the entire file is read
        while(file_content):
                for i in range(len(widths)):   # will run from 0 to 9 for length 10
                        # Travserse till the end of columns we want in one line
                        # Formulate one text block for each per line containing data in fixed width, each text width of data seperated by offsets.

                        # For the first column, this will work as file_content[(0*5):(1*5)] which means to extract f_width chars
                        # After that, an offset widths[0] is added to it. Both these combined forms the first column of width f_width
                        # with offset being the separation between first and second column

                        # For the second column, the pointer will be at 4 since the first 5 characters have already been extracted and it starts from 0
                        # We now need to move the pointer from 5-10 ie [(1*5):(2*5)] which will extract the next 5 characters from file_content.

                        # This process is reapeated until we have extracted the entire file content
			# Update the file_content removing what has been extracted
                        block = block + file_content[i*f_width:(i+1)*f_width]+(" "*(widths[i]))

                # Add newline after the block is extracted
                block = block + '\n'

                # Update file_content
                file_content = file_content[(i+1)*f_width:]

        # Write the block to the output file in the mounted output directory ie /var/output
        total = header_block + '\n' + block
        fwp.write(total)
        fwp.close()

# Iterate each in ipDir
for filename in os.listdir(ipDir):
	if not(filename.startswith('.')):
        	#print(filename)
        	fixed_width_generator(ipDir + filename)

def generate_csv(input_file):
        # Take out the base filename
        basefile = input_file.split('/')[-1].split('.')[0]
        with open(input_file, encoding=f_width_enc) as f:
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
                                #print("Length is equal to 10 ie "+str(len(val)))
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
                        else:
                                # value length exceeds no of columns headers
                                print("Error, shouldn't be the case ..")
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
		#print(filename)
		generate_csv(opDir + filename)

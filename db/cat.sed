#!/usr/bin/sed -f

# Append each line to the "hold space" (a temporary buffer)
H

# If the last line ends with a line break, it means it's not the end of a paragraph.
# We remove the line break, append the next line, and continue this process.
$!d

# At the end of the stream, we swap the "pattern space" (current line) with the "hold space"
# and perform the necessary replacements to merge the lines together.
x
s/\n/\\n/g
p

# Clear the pattern space for the next cycle
s/.*//


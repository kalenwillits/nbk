# nbk
Simple terminal notebook application using Python pandas to store
markdown notes and use Vim to edit them in the command line. 

This has only been tested on Ubuntu.

# Install
1. Clone the repository and move into it.
```
git clone git@github.com:KalenWillits/nbk.git
cd nbk
```
2. Create the python virtual environment and install dependencies.
```
python -m venv .nbk
source activate
pip install -r requirements.txt
```
Note that x-clip is a dependency for using the snippet function

3. Compile the executable and install it to your .bashrc.
```
source compile.sh
source install.sh
```
4. If it went well, the `nbk` command will be available anywhere in you system.


# Usage

## Creating a note
```
nbk -c
```
This will open the editor and save it to the data folder when closed.

## Querying notes
```
nbk
```
This will display the default view, which is all notes that have been created or edited today.
If only one note is found, the contents of the note is printed to the terminal. If multiple notes are found, a pandas
table is built and displayed at the terminal.

```
nbk -a
```
Using the <-a> flag will display all notes. This flag will ignore other crud operations.


The positional argument following `nbk` is a query string. This query string is in the style of url query string with
some inspiration from the Django ORM.
Available fields to query on the Note model are as follows:
- title: The first line of the note and preview in a view.
- page: The page number of the note. This can be used to quickly look up unique notes, however this field is dynamic
and will change as the notebook becomes larger or smaller. 
- note: The body of the note.
- timestamp: A float representing the epoch time of when the note was last modified.
- year, month, day, weekday, hour: These are all derived from the timestamp field.

The query syntax starts each field with a question mark, followed by a field name, an optional function, and then an 
equals sign pointing at the input value.
```
?<field><func>=<value>
```
A query where we are looking for the first page and the first page only of the notebook would look like this:
```
nbk ?page=1
```
The result is the first page of the notebook if it exists .

For more specific queries, you could use a function. Some common supported functions are:
- `__f`: Finds if a substring is within the field.
- `__ne`: Checks if the value is not equal to the field.
- `__gt`: Greater than
- `__lt`: Less than
- `__gte`: Greater than or equal to 
- `__lte`: Less than or equal to

To find all pages larger that 1, you could use this:
```
nbk ?page__gt=1
```

You can also string queries together. To find all pages greater than one that contain the word "code" in their body,
you would use this:
```
nbk ?page__gt=1&note__f=code
```

## Editing a note
To edit a note, use the update flag <-u> at the end of a query string.
```
nbk ?page=1 -u
```
The update flag will not work if the query returns multiple notes.

## Deleting a note
It is possible to delete multiple notes at once, so be careful when writing queries. Delete all notes from the resulting
query by adding the drop <-d> flag at the end of a query.
```
nbk ?page=1 -d
```
You will be prompted if you really want to continue your action before the deletion occurs.

## Creating a snippet
Snippets are parts of a note that can contain variables which can be replaced and copied to the clipboard. A note with
a format string will look like this:
```
`````
	My name is {0}
	I am a {1}
`````
```

Everything within the tildes will be the part of the note that is copied and formatted. You can pass the arguments in 
a string right after the snippet <-s> flag like so:
```
nbk ?page=1 -s "Name;Salesman"
```
Any number of arguments can be passed, each one separated by the semi-colon delimiter. However, an error will be thrown
if your format variable looks for an index higher than your arguments contain.

## Executing a snippet

Executing a snippet works just as copying a snippet, except it does not copy it the clipboard. Instead it expects the 
snippet to be a valid bash script and will execute the snippet directly in the operating system. 

```
nbk ?title=find_files -e ".py"
```

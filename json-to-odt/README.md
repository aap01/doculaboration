# json-to-odt

Generates Openoffice odt from json generated through **gsheet-to-json**

copy ```conf/config.yml.dist``` as ```conf/config.yml``` and do not commit the copied file

## we need an application macro
Create the following macro from *Tools->Macros->Edit Macros...*

* Container **My Macros & Dialogs**
* Application **Standard**
* Module **Module1**
* Function **open_document(String)**

```
Sub open_document(docUrl As String)

	Dim doc As Object
	Dim properties(1) As New com.sun.star.beans.PropertyValue

	properties(0).Name = "Hidden"
	properties(0).value  = true
	properties(1).Name = "MacroExecutionMode"
	properties(1).value  = 4

	doc = StarDesktop.loadComponentFromURL(docUrl, "_blank", 0, properties)

	'''Update indexes, such as for the table of contents'''
	Dim i As Integer

    With doc
        If .supportsService("com.sun.star.text.GenericTextDocument") Then
            For i = 0 To .getDocumentIndexes().count - 1
                .getDocumentIndexes().getByIndex(i).update()
            Next i
        End If
    End With

	doc.store()
	doc.close(True)

End Sub
```

## Useful links
some useful links for json-to-odt
* https://mashupguide.net/1.0/html/ch17s04.xhtml
* https://github.com/eea/odfpy/tree/master/examples
* https://glot.io/snippets/f0nuzv7b8k

## Linux usage:
```
DOCULABORATION_BASE="/home/asif/projects/asif@github/doculaboration"
cd ${DOCULABORATION_BASE}
cd ./json-to-odt/src
./odt-from-json.py --config '../conf/config.yml'
```

## Windows usage:
```
set DOCULABORATION_BASE="D:\projects\asif@github\doculaboration"
cd %DOCULABORATION_BASE%
cd ./json-to-odt/src
python odt-from-json.py --config "../conf/config.yml"
```
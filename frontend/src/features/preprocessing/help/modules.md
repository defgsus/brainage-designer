## Preprocessing modules 

In this view, modules can be added, edited, moved or deleted.

Modules generate or process **objects** which are typically brain images but can be any type of file or data.

Each preprocessing pipeline consists of these stages of modules:

### Source

These modules will one-by-one send objects (images) to the further pipeline stages. 

### Filter

The objects that will be processed further can be filtered here.

### Processing

The actual processing of objects happens in this stage. The order of processing is from **top to bottom**. 
You can drag/drop the modules to change the order of processing.

The **last module** will store all resulting objects into the pipeline's **target path**. 

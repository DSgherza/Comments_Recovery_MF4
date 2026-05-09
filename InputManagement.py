import asammdf

class InputManagement:

    def __init__(self, filename):
        mdf_file = asammdf.MDF(filename)
        self.log = filename.split("/")[-1]
        self.comment = mdf_file.header.description.replace("\n",". ")
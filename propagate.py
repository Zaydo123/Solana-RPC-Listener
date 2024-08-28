""" 
Propagate.py
By Zayd Alzein
License: MIT

Description:
This is a simple script that will propigate
the respective environment variables to the
respective directories that need them.
The primary use is for prisma db connections
"""

import os

mappings = {
    "DATABASE_URL": "apps/prisma/.env",
    "POSTGRES_DB": "apps/prisma/.env",
    "POSTGRES_USER": "apps/prisma/.env",
    "POSTGRES_PASSWORD": "apps/prisma/.env",
}

def main():
    try:
        with open(os.getcwd()+"/.env", "r") as f:
            for line in f:
                # ignore comments
                if line.strip(" ").startswith("#"):
                    continue
                elif line.strip(" ") == "\n":
                    continue
                else:
                    split = line.split("=")
                    key = split[0].strip()
                    value = "=".join(split[1:]).strip()
                    mapping = mappings.get(key, False)
                    if mapping != False:
                        with open(os.getcwd()+"/"+str(mapping), "r+") as f:
                            # read all lines in file
                            lines = f.readlines()
                            # check if key exists, if so, update it, else append it
                            found = False
                            for i, line in enumerate(lines):
                                if line.startswith(key):
                                    lines[i] = f"{key}={value}\n"
                                    found = True
                                    break
                            if not found:
                                lines.append(f"{key}={value}\n")
                            f.seek(0)
                            f.writelines(lines)
                            f.truncate()
        
    except FileNotFoundError as e:
        print("File not found: ", e)
        return
    except Exception as e:
        print("An error occured: ", e)
        return

if __name__ == "__main__":
    main()
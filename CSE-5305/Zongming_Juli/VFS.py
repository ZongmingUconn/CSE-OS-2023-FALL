# Virtual File System via Python Ver.2.0


class VirtualFileSystem:   
    def __init__(self):
        # Initialize a virtual file system instance, including user, root directory, current directory,
        # open files, path tracking, virtual disk space, FAT table and next free space pointer.
        self.current_user = None
        self.root = {}  # Root directory containing user directory entries
        self.current_dir = None
        self.open_files = {}
        self.path = []  # To keep track of the current path
        self.disk_space = bytearray(1024 * 1024)  # 1MB of virtual disk space
        self.fat_table = {}  # FAT Table
        self.next_free_space = 0  # Pointer to the next free space on disk


    def display_operations(self):
        # Displays the available commands to the user.
        print("Welcome to the Virtual File System. Here are the available commands:")
        print("  register [username] [password]   - Register a new user")
        print("  login [username] [password]      - Login as a user")
        print("  logout                           - Logout from the current user")
        print("  dir                              - List directories and files")
        print("  create [filename]                - Create a new file")
        print("  del [filename]                   - Delete a file")
        print("  open [filename]                  - Open a file")
        print("  close [filename]                 - Close a file")
        print("  read [filename]                  - Read a file's content")
        print("  write [filename] [content]       - Write content to a file")
        print("  cd [dirname]                     - Change directory")
        print("  md [dirname]                     - Make a new directory")
        print("  rd [dirname]                     - Remove a directory")
        print("  diskusage                        - Display disk usage")
        print("  showfat                          - Show FAT table")
        print("Type 'exit' to quit the program.")

    def _build_file_paths(self, current_dir, current_path=""):
        # Full path to build file
        file_paths = {}
        for name, item in current_dir["children"].items():
            path = current_path + "/" + name
            if item["type"] == "file":
                file_paths[name] = path
            elif item["type"] == "dir":
                file_paths.update(self._build_file_paths(item, path))
        return file_paths

    def show_fat_table(self):
        # Displays the file allocation table (FAT table), which shows the start and end positions of each file.
        file_paths = self._build_file_paths(self.root[self.current_user]["FAT"])
        print("FAT Table:")
        for filename, (start, end) in self.fat_table.items():
            path = file_paths.get(filename, "Unknown")
            print(f"  {filename}:")
            print(f"    Path: {path}")
            print(f"    Start - {start}, End - {end}")

    def display_disk_usage(self):
        # Show current disk usage
        used_space = sum(len(self.disk_space[start:end]) for start, end in self.fat_table.values())
        total_space = len(self.disk_space)
        print(f"Disk usage: {used_space}/{total_space} bytes")

    def register(self, username, password):
        # Allows a new user to register in the system.
        if username in self.root:
            return "User already exists."
        else:
            self.root[username] = {
                "username": username,
                "password": password,
                "FAT": {"type": "dir", "children": {}}  # User File Allocation Table (FAT)
            }
            return f"User '{username}' registered successfully."

    def login(self, username, password):
        # Handles the login functionality for a user.
        if username in self.root and self.root[username]["password"] == password:
            self.current_user = username
            self.current_dir = self.root[username]["FAT"]  # Point to the user's FAT
            self.path = []
            return f"User '{username}' logged in successfully."
        else:
            return "Login failed."

    def logout(self):
        # Logs out the current user from the system.
        if self.current_user:
            user = self.current_user
            self.current_user = None
            self.current_dir = None
            self.path = []
            return f"User '{user}' logged out successfully."
        else:
            return "No user currently logged in."

    def dir(self):
        # Lists the directories and files in the current directory.
        return list(self.current_dir["children"].keys())

    def create(self, filename):
        # Creates a new file in the current directory.
        if filename not in self.current_dir["children"]:
            self.current_dir["children"][filename] = {"content": "", "type": "file"}
            self.fat_table[filename] = (self.next_free_space, self.next_free_space)  # initial allocation
            return f"File '{filename}' created."
        else:
            return "File already exists."

    def delete(self, filename):
        # Deletes a file from the current directory.
        if filename in self.current_dir["children"]:
            del self.current_dir["children"][filename]
            file_start, file_end = self.fat_table[filename]
            self.disk_space[file_start:file_end] = bytearray(file_end - file_start)  # Clear data on disk
            self.next_free_space = file_start  # Update the next free space pointer
            del self.fat_table[filename]
            self.show_fat_table()  
            return f"File '{filename}' deleted."
        else:
            return "File not found."

    def open(self, filename):
        # Opens a file for reading or writing.
        if filename in self.current_dir["children"] and filename not in self.open_files:
            self.open_files[filename] = self.current_dir["children"][filename]
            return f"File '{filename}' opened."
        else:
            return "File not found or already opened."

    def close(self, filename):
        # Closes an opened file.
        if filename in self.open_files:
            del self.open_files[filename]
            return f"File '{filename}' closed."
        else:
            return "File not opened."

    def read(self, filename):
        # Reads the content of an opened file.
        if filename in self.open_files:
            return self.open_files[filename]["content"]
        else:
            return "File not opened."

    def write(self, filename, content):
        # Writes or appends content to an opened file.
        if filename in self.open_files:
            file_start, file_end = self.fat_table[filename]
            new_end = min(file_end + len(content), len(self.disk_space))
            self.disk_space[file_start:new_end] = content[:new_end - file_start].encode()
            self.open_files[filename]["content"] += content
            self.fat_table[filename] = (file_start, new_end)
            self.next_free_space = new_end
            return "Content written to file."
        else:
            return "File not opened."

    def cd(self, dirname):
        # Changes the current working directory.
        if dirname == "..":
            if self.path:
                self.path.pop()
                self._update_current_dir()
                return "Returned to the parent directory."
            else:
                return "Already at the root directory."
        elif dirname in self.current_dir["children"] and self.current_dir["children"][dirname]["type"] == "dir":
            self.path.append(dirname)
            self._update_current_dir()
            return f"Changed directory to '{dirname}'."
        else:
            return "Directory not found."

    def _update_current_dir(self):
        # Update the current working directory based on the path.
        self.current_dir = self.root[self.current_user]["FAT"]
        for dir in self.path:
            self.current_dir = self.current_dir["children"][dir]

    def rd(self, dirname):
        # Removes a directory from the current directory.
        if dirname in self.current_dir["children"] and self.current_dir["children"][dirname]["type"] == "dir":
            del self.current_dir["children"][dirname]
            return f"Directory '{dirname}' deleted."
        else:
            return "Directory not found or is a file."

    def md(self, dirname):
        # Creates a new directory in the current directory.
        if dirname not in self.current_dir["children"]:
            self.current_dir["children"][dirname] = {"type": "dir", "children": {}}
            return f"Directory '{dirname}' created."
        else:
            return "Directory already exists."

    def process_command(self, command):
        # Processes a given command by calling the appropriate method.
        args = command.split()
        if not args:
            return "No command entered."
        cmd = args[0].lower()
        
        if cmd == "diskusage":
            self.display_disk_usage()
            return ""
        elif cmd == "showfat":
            self.show_fat_table()
            return ""
    
        if cmd == "register" and len(args) == 3:
            return self.register(args[1], args[2])
        elif cmd == "login" and len(args) == 3:
            return self.login(args[1], args[2])
        elif cmd == "logout":
            return self.logout()
        elif cmd == "dir":
            return self.dir()
        elif cmd == "create" and len(args) == 2:
            return self.create(args[1])
        elif cmd == "del" and len(args) == 2:
            return self.delete(args[1])
        elif cmd == "open" and len(args) == 2:
            return self.open(args[1])
        elif cmd == "close" and len(args) == 2:
            return self.close(args[1])
        elif cmd == "read" and len(args) == 2:
            return self.read(args[1])
        elif cmd == "write" and len(args) >= 3:
            return self.write(args[1], " ".join(args[2:]))
        elif cmd == "cd" and len(args) == 2:
            return self.cd(args[1])
        elif cmd == "md" and len(args) == 2:
            return self.md(args[1])
        elif cmd == "rd" and len(args) == 2:
            return self.rd(args[1])
        else:
            return "Invalid command or incorrect number of arguments."


# Create an instance of the VirtualFileSystem
vfs = VirtualFileSystem()

# Display the operations available to the user
vfs.display_operations()

# Main loop to process user commands
while True:
    command = input("> ")
    if command.lower() == "exit":
        break
    response = vfs.process_command(command)
    print(response)

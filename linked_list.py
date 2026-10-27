"""
linked_list.py
--------------
The DSA part of the project: a SINGLY LINKED LIST that stores complaints.

    head -> [Complaint 1 | next] -> [Complaint 2 | next] -> [Complaint 3 | None]
                                                                 ^
                                                               tail

Each box is a Node. A Node holds one Complaint object and a pointer
(`next`) to the following Node. The last Node points to None.
"""


class Node:
    """One box of the linked list."""

    def __init__(self, complaint):
        self.complaint = complaint  # the data
        self.next = None            # pointer to the next node


class ComplaintLinkedList:
    """Singly linked list of complaints (oldest complaint at the head)."""

    def __init__(self):
        self.head = None   # first node
        self.tail = None   # last node (makes adding at the end quick)
        self.size = 0

    # ------------------------------------------------------------
    # INSERT: add a new complaint at the END of the list
    # ------------------------------------------------------------
    def add_complaint(self, complaint):
        new_node = Node(complaint)
        if self.head is None:          # list is empty
            self.head = new_node
            self.tail = new_node
        else:                          # attach after the current last node
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    # ------------------------------------------------------------
    # SEARCH: find a complaint by its id (linear search)
    # ------------------------------------------------------------
    def search_by_id(self, complaint_id):
        current = self.head
        while current is not None:
            if current.complaint.id == complaint_id:
                return current.complaint
            current = current.next
        return None                    # not found

    # ------------------------------------------------------------
    # DELETE: remove a complaint by its id
    # ------------------------------------------------------------
    def delete_complaint(self, complaint_id):
        current = self.head
        previous = None

        while current is not None:
            if current.complaint.id == complaint_id:
                if previous is None:             # deleting the head node
                    self.head = current.next
                else:                            # skip over the node
                    previous.next = current.next

                if current is self.tail:         # deleted the last node
                    self.tail = previous

                self.size -= 1
                return True
            previous = current
            current = current.next
        return False                   # id not found

    # ------------------------------------------------------------
    # UPDATE: change status + remark of a complaint
    # ------------------------------------------------------------
    def update_status(self, complaint_id, new_status, remark=""):
        complaint = self.search_by_id(complaint_id)
        if complaint is None:
            return False
        complaint.update_status(new_status, remark)
        return True

    # ------------------------------------------------------------
    # TRAVERSAL helpers (walk through the list from head to tail)
    # ------------------------------------------------------------
    def display_all(self):
        """Returns all complaints as a normal Python list (oldest first)."""
        result = []
        current = self.head
        while current is not None:
            result.append(current.complaint)
            current = current.next
        return result

    def filter_by_status(self, status):
        result = []
        current = self.head
        while current is not None:
            if current.complaint.status == status:
                result.append(current.complaint)
            current = current.next
        return result

    def get_by_student(self, student_id):
        result = []
        current = self.head
        while current is not None:
            if current.complaint.student_id == student_id:
                result.append(current.complaint)
            current = current.next
        return result

    def count_by_status(self):
        counts = {"Pending": 0, "In Progress": 0, "Resolved": 0}
        current = self.head
        while current is not None:
            counts[current.complaint.status] += 1
            current = current.next
        return counts

    def __len__(self):
        return self.size

<template>
  <div class="container">
    <h1>Book Management</h1>

    <!-- Form to Add a New Book -->
    <div>
      <h2>Create New Book</h2>
      <form @submit.prevent="createBook">
        <input v-model="newBook.title" type="text" placeholder="Title" required />
        <input v-model="newBook.author" type="text" placeholder="Author" required />
        <input v-model="newBook.year" type="number" placeholder="Year" required />
        <button type="submit">Add Book</button>
      </form>
    </div>

    <!-- Book List -->
    <div>
      <h2>Book List</h2>
      <ul>
        <li v-for="book in books" :key="book.id">
          <div>
            <strong>{{ book.title }}</strong> by {{ book.author }} ({{ book.year }})
            <button @click="editBook(book.id)">Edit</button>
            <button @click="deleteBook(book.id)">Delete</button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Book Update Modal -->
    <div v-if="showUpdateModal">
      <h2>Edit Book</h2>
      <form @submit.prevent="updateBook">
        <input v-model="updatedBook.title" type="text" placeholder="Title" required />
        <input v-model="updatedBook.author" type="text" placeholder="Author" required />
        <input v-model="updatedBook.year" type="number" placeholder="Year" required />
        <button type="submit">Update Book</button>
        <button @click="showUpdateModal = false">Cancel</button>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      books: [],
      newBook: {
        title: '',
        author: '',
        year: null,
      },
      updatedBook: {
        title: '',
        author: '',
        year: null,
      },
      showUpdateModal: false,
      editingBookId: null,
    };
  },
  methods: {
    // Fetch books from the API
    async fetchBooks() {
      try {
        const response = await fetch('http://localhost:8000/books/');
        const data = await response.json();
        this.books = data;
      } catch (error) {
        console.error('Error fetching books:', error);
      }
    },

    // Create a new book
    async createBook() {
      try {
        const response = await fetch('http://localhost:8000/books/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.newBook),
        });
        if (response.ok) {
          const createdBook = await response.json();
          this.books.push(createdBook);
          this.newBook = { title: '', author: '', year: null }; // Reset the form
        } else {
          console.error('Error creating book');
        }
      } catch (error) {
        console.error('Error creating book:', error);
      }
    },

    // Open the edit modal and set the current book data for editing
    editBook(bookId) {
      const book = this.books.find((book) => book.id === bookId);
      if (book) {
        this.updatedBook = { ...book }; // Copy the book's data
        this.editingBookId = bookId;
        this.showUpdateModal = true;
      }
    },

    // Update the book
    async updateBook() {
      try {
        const response = await fetch(`http://localhost:8000/books/${this.editingBookId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.updatedBook),
        });

        if (response.ok) {
          const updatedBook = await response.json();
          const index = this.books.findIndex((book) => book.id === this.editingBookId);
          this.books[index] = updatedBook;
          this.showUpdateModal = false;
        } else {
          console.error('Error updating book');
        }
      } catch (error) {
        console.error('Error updating book:', error);
      }
    },

    // Delete a book
    async deleteBook(bookId) {
      try {
        const response = await fetch(`http://localhost:8000/books/${bookId}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          this.books = this.books.filter((book) => book.id !== bookId);
        } else {
          console.error('Error deleting book');
        }
      } catch (error) {
        console.error('Error deleting book:', error);
      }
    },
  },

  // Fetch the book list when the component is mounted
  mounted() {
    this.fetchBooks();
  },
};
</script>

<style scoped>
.container {
  width: 80%;
  margin: auto;
}

form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

input {
  padding: 8px;
  font-size: 14px;
}

button {
  padding: 8px;
  font-size: 14px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  margin-bottom: 10px;
}

div {
  margin-bottom: 10px;
}

div button {
  margin-left: 10px;
}
</style>

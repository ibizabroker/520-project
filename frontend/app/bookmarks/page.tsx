"use client";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import ProtectedRoute from "../components/ProtectedRoute";
import { useState, useEffect } from "react";
import RecipePageList from "../components/RecipePageList";
import { Post } from "../types";

export default function Bookmarks() {
  const [bookmarkedRecipes, setBookmarkedRecipes] = useState<Post[]>([]);

  useEffect(() => {
    const fetchBookmarkedRecipes = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/posts", {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setBookmarkedRecipes(data.posts);
          console.log(data)
        } else {
          console.error("Failed to fetch bookmarked recipes.");
        }
      } catch (error) {
        console.error("Error fetching bookmarks:", error);
      }
    };

    fetchBookmarkedRecipes();
  }, []);

  return (
    <ProtectedRoute allowedRoles={[true]}>
      <div className="min-h-screen flex flex-col bg-black">
        <Navbar />
        <main className="flex-grow p-6">
          <div className="mb-6">
            <h1 className="flex justify-center text-3xl font-bold text-white">Your Bookmarked Recipes</h1>
          </div>

          <div className="flex justify-center">
            <div className="w-full max-w-4xl">
              {bookmarkedRecipes.length > 0 ? (
                bookmarkedRecipes.map((post, index) => (
                  <div key={index} className="mb-6">
                    <RecipePageList post={post} />
                  </div>
                ))
              ) : (
                <p className="text-gray-400 text-center">No bookmarked recipes found.</p>
              )}
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </ProtectedRoute>
  );
};

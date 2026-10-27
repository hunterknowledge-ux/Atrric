package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	_ "github.com/mattn/go-sqlite3"
)

type Building struct {
	ID       int64   `json:"id"`
	Name     string  `json:"name"`
	Height   float64 `json:"height"`
	Lat      float64 `json:"lat"`
	Lon      float64 `json:"lon"`
}

func main() {
	fmt.Println("[ATRRIC] Spatial Go Engine running on :8081")
	http.HandleFunc("/api/buildings", handleBuildings)
	log.Fatal(http.ListenAndServe("127.0.0.1:8081", nil))
}

func handleBuildings(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	db, err := sql.Open("sqlite3", "./spatial_cache.db")
	if err != nil {
		http.Error(w, `{"error":"DB Error"}`, 500)
		return
	}
	defer db.Close()

	// Ambil maksimum 200 bangunan untuk elak crash phone
	rows, err := db.Query("SELECT id, name, height, lat, lon FROM buildings LIMIT 200")
	if err != nil {
		http.Error(w, `{"error":"Query Error"}`, 500)
		return
	}
	defer rows.Close()

	var buildings []Building
	for rows.Next() {
		var b Building
		rows.Scan(&b.ID, &b.Name, &b.Height, &b.Lat, &b.Lon)
		buildings = append(buildings, b)
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"type": "geojson",
		"data": buildings,
	})
}
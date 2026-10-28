package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	fmt.Println("[ATRRIC] Go Server running on :8081")
	http.HandleFunc("/api/projects", handleProjects)
	http.HandleFunc("/api/analytics", handleAnalytics)
	log.Fatal(http.ListenAndServe("127.0.0.1:8081", nil))
}

// Endpoint untuk Peta (Data Center)
func handleProjects(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")
	db, _ := sql.Open("sqlite3", "./spatial_cache.db")
	defer db.Close()

	rows, _ := db.Query("SELECT id, name, type, lat, lon FROM real_projects")
	defer rows.Close()

	var result []map[string]interface{}
	for rows.Next() {
		var id, name, typ string
		var lat, lon float64
		rows.Scan(&id, &name, &typ, &lat, &lon)
		result = append(result, map[string]interface{}{
			"id": id, "name": name, "type": typ, "lat": lat, "lon": lon,
		})
	}
	json.NewEncoder(w).Encode(map[string]interface{}{"data": result})
}

// Endpoint untuk Analytics (MIDA & IPI)
func handleAnalytics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")
	db, _ := sql.Open("sqlite3", "./spatial_cache.db")
	defer db.Close()

	// 1. Ambil MIDA (Kalau ada)
	rows, _ := db.Query("SELECT state, projects, investment FROM mida_stats")
	var mida []map[string]interface{}
	for rows.Next() {
		var state string
		var proj int
		var inv float64
		rows.Scan(&state, &proj, &inv)
		mida = append(mida, map[string]interface{}{"state": state, "projects": proj, "investment": inv})
	}
	rows.Close()

	// 2. Ambil IPI
	rows, _ = db.Query("SELECT date, sector, ipi_index FROM ipi_stats ORDER BY date ASC")
	var ipi []map[string]interface{}
	for rows.Next() {
		var date, sector string
		var idx float64
		rows.Scan(&date, &sector, &idx)
		ipi = append(ipi, map[string]interface{}{"date": date, "sector": sector, "index": idx})
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"mida": mida,
		"ipi":  ipi,
	})
}
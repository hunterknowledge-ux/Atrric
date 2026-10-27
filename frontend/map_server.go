package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

// Struct ni untuk hantar balik ke frontend
type WSMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
	Time string      `json:"time"`
}

func main() {
	fmt.Println("[ATRRIC] Live Spatial Go Server running on :8081")
	
	// Handle WebSocket connection
	http.HandleFunc("/ws", handleWebSocket)
	
	log.Fatal(http.ListenAndServe("127.0.0.1:8081", nil))
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	// Kita guna HTTP Polling fallback sementara sebab WebSocket library
	// memerlukan external package (gorilla/websocket). 
	// Untuk pure stdlib Go, kita buat Server-Sent Events (SSE) atau Polling.
	// Tapi supaya kau boleh test sekarang tanpa install package luar, 
	// kita guna standard JSON API yang di-poll oleh frontend.
	
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	lat := r.URL.Query().Get("lat")
	lng := r.URL.Query().Get("lng")

	if lat == "" || lng == "" {
		http.Error(w, `{"error":"missing coordinates"}`, 400)
		return
	}

	data := fetchOverpass(lat, lng)
	json.NewEncoder(w).Encode(data)
}

func fetchOverpass(lat, lng string) WSMessage {
	// Query kecil sekitar koordinat
	query := fmt.Sprintf(`
		[out:json][timeout:10];
		way["building"="construction"](around:2000,%s,%s);
		out geom 50;
	`, lat, lng)

	resp, err := http.Post("https://overpass-api.de/api/interpreter", "text/plain", 
		&stringReader{query, 0})
	
	if err != nil {
		return WSMessage{Type: "error", Data: err.Error(), Time: time.Now().Format("15:04:05")}
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)
	
	var raw map[string]interface{}
	json.Unmarshal(body, &raw)

	return WSMessage{
		Type: "geojson",
		Data: raw["elements"],
		Time: time.Now().Format("15:04:05"),
	}
}

// Simple custom string reader untuk POST body
type stringReader struct {
	s string
	i int64
}

func (r *stringReader) Read(b []byte) (n int, err error) {
	if r.i >= int64(len(r.s)) {
		return 0, fmt.Errorf("EOF")
	}
	n = copy(b, r.s[r.i:])
	r.i += int64(n)
	return
}
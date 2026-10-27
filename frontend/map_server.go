package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

type WSMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
	Time string      `json:"time"`
}

func main() {
	fmt.Println("[ATRRIC] Live Building Tracker running on :8081")
	http.HandleFunc("/ws", handleWebSocket)
	log.Fatal(http.ListenAndServe("127.0.0.1:8081", nil))
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	lat := r.URL.Query().Get("lat")
	lng := r.URL.Query().Get("lng")
	
	// Radius 5KM (untuk elak timeout)
	radius := "5000"

	if lat == "" || lng == "" {
		http.Error(w, `{"error":"missing coordinates"}`, 400)
		return
	}

	data := fetchBuildings(lat, lng, radius)
	json.NewEncoder(w).Encode(data)
}

func fetchBuildings(lat, lng, radius string) WSMessage {
	// QUERY PENTING: Ambil SEMUA bangunan yang ada "name"
	query := fmt.Sprintf(`
		[out:json][timeout:20];
		(
		  way["building"]["name"](around:%s,%s,%s);
		  way["building:construction"]["name"](around:%s,%s,%s);
		);
		out geom 150;
	`, radius, lat, lng, radius, lat, lng)

	resp, err := http.Post("https://overpass-api.de/api/interpreter", "text/plain", &stringReader{query, 0})
	
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
var urls = [document.URL, ""];
var time_out = 1;
var sections = document.getElementsByClassName("sc-ciSmjq");
function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function getUrls() { 
	for (let s of sections) {
		s_videos = s.childNodes[1].childNodes;
		s_title = s.childNodes[0].childNodes[1].childNodes[0].innerText;
		urls.push(s_title);
		
		for (let j=0; j<s_videos.length; j++) {
			if(s_videos[j].className.includes("locked")) { continue; }
			v_time = s_videos[j].childNodes[2].innerText;
			urls.push(v_time);
			s_videos[j].click();
			await get_iframe(time_out);
		}

		if(s != sections[sections.length-1]) { urls.push(""); }
	}
	return urls;
}

async function get_iframe(t_out) {
	try {
  		i_frame = await document.getElementsByTagName('iframe')[0].src.toString();
		urls.push(urls.pop() + " | " + i_frame);
	}
	catch(err) {
		//console.error(err);
		await sleep(t_out);
		return await get_iframe(t_out); 
	}
}

async function download(){
	var text = await getUrls();
	var a = document.createElement("a");
	a.href = window.URL.createObjectURL(new Blob([text.join('\n')], {type:"text/plain;encoding:utf-8"}));
	a.download = "url.txt";
	a.click();
}

download();

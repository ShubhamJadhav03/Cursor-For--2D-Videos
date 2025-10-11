import { useEffect, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  horizontalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Save, Download, X } from 'lucide-react';
// --- Sortable Scene (Left Panel) ---
function SortableScene({ scene, onPreview }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: scene.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => onPreview(scene)}
      className="rounded-md bg-gray-800 px-3 py-2 text-sm text-gray-200 cursor-pointer select-none border border-gray-700 hover:bg-gray-700 transition-colors mb-2"
      title="Click to preview or drag to timeline"
    >
      {scene.name}
    </div>
  );
}

// --- Sortable Timeline Item (Center Panel Chips) ---
function SortableTimelineItem({ item, index, onDelete }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="relative inline-flex items-center gap-2 rounded-full border border-gray-600 bg-gray-700 px-3 py-1 text-xs text-white cursor-grab group transition-transform duration-200"
    >
      <span className="opacity-70">#{index + 1}</span>
      <span>{item.name}</span>

      {/* Delete Button */}
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onDelete();
        }}
        {...{
          onPointerDown: (e) => e.stopPropagation(),
          onMouseDown: (e) => e.stopPropagation(),
          onTouchStart: (e) => e.stopPropagation(),
        }}
        className="absolute -top-2 -right-2 hidden group-hover:flex items-center justify-center rounded-full bg-red-600 hover:bg-red-500 p-1 opacity-0 group-hover:opacity-100 transition-all duration-200"
        title="Remove"
      >
        <X size={12} />
      </button>
    </div>
  );
}

// --- Main Component ---
export default function VideoSceneBuilder() {
  const [scenes, setScenes] = useState([]); // Start with an empty list
  const [timeline, setTimeline] = useState([]);
  const [logs, setLogs] = useState(["System initialized."]);
  const [desc, setDesc] = useState("");
  const [previewUrl, setPreviewUrl] = useState(""); // ✅ new preview state
  const [isGenerating, setIsGenerating] = useState(false);
  const logsRef = useRef(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (message) => {
    setLogs((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] ${message}`,
    ]);
  };

  // ✅ Scene preview handler
  const handlePreviewScene = (scene) => {
    if (!scene.url) {
      addLog(`"${scene.name}" has no video yet.`);
      return;
    }
    setPreviewUrl(scene.url);
    addLog(`Previewing: ${scene.name}`);
  };

  // --- Drag and Drop Logic ---
  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over) return;

    const sourceScene = scenes.find((scene) => scene.id === active.id);
    const sourceTimelineIndex = timeline.findIndex(
      (item) => item.id === active.id
    );

    if (sourceScene) {
      const newTimelineItem = {
        ...sourceScene,
        id: `timeline-${crypto.randomUUID()}`,
      };
      setTimeline((prev) => [...prev, newTimelineItem]);
      addLog(`Added "${sourceScene.name}" to timeline.`);
      return;
    }

    if (sourceTimelineIndex !== -1) {
      const overTimelineIndex = timeline.findIndex(
        (item) => item.id === over.id
      );
      if (overTimelineIndex !== -1 && sourceTimelineIndex !== overTimelineIndex) {
        setTimeline((items) =>
          arrayMove(items, sourceTimelineIndex, overTimelineIndex)
        );
        addLog(`Reordered timeline.`);
      }
    }
  };

  // --- Add Scene ---


// And REPLACE it with this new version:
  const handleAddScene = async () => {
      const trimmed = desc.trim();
      if (!trimmed) return;

      // Set loading state and log the start
      setIsGenerating(true);
      addLog(`🎬 Requesting scene: "${trimmed}"...`);
      
      try {
        // --- API Call to Your Backend ---
        const response = await fetch('http://localhost:8000/generate-scene/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: trimmed }),
        });

        if (!response.ok) {
          // If the backend returns an error, show it
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Backend failed to generate video.');
        }

        // Get the video file from the response
        const videoBlob = await response.blob();
        const videoUrl = URL.createObjectURL(videoBlob);

        // Create the new scene object with the real video URL
        const newScene = {
          id: `scene-${crypto.randomUUID()}`,
          name: trimmed,
          url: videoUrl, // <-- The scene now has a real video URL
        };

        // Add the new scene to the bin and set it as the preview
        setScenes((s) => [...s, newScene]);
        setPreviewUrl(videoUrl);
        addLog(`✅ Scene "${trimmed}" generated successfully!`);
        setDesc("");

      } 
      catch (error) 
      {
        console.error("Generation failed:", error);
        addLog(`❌ ERROR: ${error.message}`);
      } 
      finally {
        // Reset loading state
        setIsGenerating(false);
      }
  };

  const handleDeleteFromTimeline = (id) => {
    setTimeline((prev) => prev.filter((item) => item.id !== id));
    addLog(`Removed a scene from timeline.`);
  };

  const handleSave = () => addLog(`Saved timeline with ${timeline.length} scenes.`);

  const handleDownload = async () => {
    if (timeline.length === 0) {
      addLog("⚠️ Timeline is empty. Add scenes to create a story.");
      return;
    }

    setIsDownloading(true);
    addLog(`🚀 Starting story generation...`);

    try {
      // Step 1: Upload each clip to the backend
      addLog(`Uploading ${timeline.length} clips...`);
      const uploadPromises = timeline.map(async (scene) => {
        // Fetch the video data from its blob URL
        const response = await fetch(scene.url);
        const videoBlob = await response.blob();
        
        // Create form data to send the file
        const formData = new FormData();
        formData.append("file", videoBlob, `${scene.id}.mp4`);

        // Upload the clip
        const uploadResponse = await fetch('http://localhost:8000/upload-clip/', {
          method: 'POST',
          body: formData,
        });

        if (!uploadResponse.ok) {
          throw new Error(`Failed to upload clip for scene: ${scene.name}`);
        }
        const data = await uploadResponse.json();
        return data.file_path; // Return the server-side file path
      });

      // Wait for all uploads to complete
      const filePaths = await Promise.all(uploadPromises);
      addLog("✅ All clips uploaded successfully.");

      // Step 2: Request the backend to stitch the clips
      addLog("🎬 Stitching video... (This may take a moment)");
      const stitchResponse = await fetch('http://localhost:8000/stitch-story/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_paths: filePaths }),
      });

      if (!stitchResponse.ok) {
        const errorData = await stitchResponse.json();
        throw new Error(errorData.detail || "Backend failed to stitch the story.");
      }

      // Step 3: Download the final video
      const finalVideoBlob = await stitchResponse.blob();
      const finalVideoUrl = URL.createObjectURL(finalVideoBlob);

      // Create a temporary link to trigger the download
      const a = document.createElement('a');
      a.href = finalVideoUrl;
      a.download = "final_story.mp4";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(finalVideoUrl); // Clean up the blob URL

      addLog("✨ Story downloaded successfully!");

    } catch (error) {
      console.error("Download failed:", error);
      addLog(`❌ ERROR: ${error.message}`);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <section className="w-full min-h-screen bg-black text-gray-300 font-sans">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <div className="mx-auto max-w-full p-4 lg:p-6 h-full">
          <div className="flex flex-col gap-4 lg:flex-row lg:gap-6 h-full">
            {/* --- Left Panel --- */}
            <aside className="w-full lg:w-1/5 rounded-lg border border-gray-700 bg-gray-900/50 flex flex-col">
              <header className="px-4 py-3 border-b border-gray-700">
                <h2 className="text-sm font-semibold text-white">
                  All The Scenes Generated
                </h2>
              </header>
              <div className="p-3 overflow-y-auto flex-grow" aria-label="All Scenes">
                <SortableContext
                  items={scenes.map((scene) => scene.id)}
                  strategy={verticalListSortingStrategy}
                >
                  {scenes.map((scene) => (
                    <SortableScene
                      key={scene.id}
                      scene={scene}
                      onPreview={handlePreviewScene} // ✅ click-to-preview
                    />
                  ))}
                </SortableContext>
              </div>
            </aside>

            {/* --- Center Panel --- */}
            <main className="w-full lg:w-3/5 flex flex-col gap-4">
              {/* ✅ Dynamic Preview Area */}
              <div className="rounded-lg border border-gray-700 bg-gray-900/50 p-6 flex items-center justify-center min-h-[240px]">
                {previewUrl ? (
                  <video
                    key={previewUrl}
                    src={previewUrl}
                    controls
                    autoPlay
                    muted
                    className="w-full max-h-[320px] rounded-md border border-gray-600"
                  />
                ) : (
                  <span className="text-sm text-gray-500">Scene Preview Area</span>
                )}
              </div>

              {/* Timeline Area */}
              <div
                className="rounded-lg border-2 border-dashed border-gray-700 p-4 transition-colors min-h-[240px] bg-gray-900/30 flex-grow"
                aria-label="Timeline drop zone"
              >
                {timeline.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <span className="text-sm text-gray-500">
                      Timeline — Drop scenes here to build your story
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    <SortableContext
                      items={timeline.map((item) => item.id)}
                      strategy={horizontalListSortingStrategy}
                    >
                      {timeline.map((item, i) => (
                        <SortableTimelineItem
                          key={item.id}
                          item={item}
                          index={i}
                          onDelete={() => handleDeleteFromTimeline(item.id)}
                        />
                      ))}
                    </SortableContext>
                  </div>
                )}
              </div>

              {/* Save & Download */}
              <div className="flex items-center gap-3">
            <button
                onClick={handleSave}
                className="inline-flex items-center gap-2 rounded-md border border-gray-700 bg-gray-800 px-4 py-2 text-sm hover:bg-gray-700 transition-colors"
            >
                <Save size={16} /> Save
            </button>
            <button
                onClick={handleDownload}
                disabled={isDownloading}
                className="inline-flex items-center gap-2 rounded-md border border-gray-700 bg-gray-800 px-4 py-2 text-sm hover:bg-gray-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
            >
                {isDownloading ? (
                    <>
                        <span className="animate-spin h-4 w-4 border-2 border-t-transparent rounded-full"></span>
                        Stitching...
                    </>
                ) : (
                    <>
                        <Download size={16} /> Download
                    </>
                )}
            </button>
        </div>
            </main>

            {/* --- Right Panel --- */}
            <aside className="w-full lg:w-1/5 flex flex-col gap-4">
              {/* Logs Section */}
              <section className="rounded-lg border border-gray-700 bg-gray-900/50 flex flex-col h-[300px]">
                <header className="px-4 py-3 border-b border-gray-700">
                  <h3 className="text-sm font-semibold text-white">Logs</h3>
                </header>
                <div
                  ref={logsRef}
                  className="p-3 overflow-y-auto flex-grow scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800"
                >
                  <ul className="space-y-2">
                    {logs.map((line, idx) => (
                      <li
                        key={idx}
                        className="text-xs text-gray-400 font-mono whitespace-pre-wrap"
                      >
                        {line}
                      </li>
                    ))}
                  </ul>
                </div>
              </section>

              {/* Scene Creation Section */}
              <section className="rounded-lg border border-gray-700 bg-gray-900/50 p-4">
                <label
                  htmlFor="scene-desc"
                  className="block text-sm font-medium mb-2 text-white"
                >
                  Enter Scene Description
                </label>
                <textarea
                  id="scene-desc"
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="w-full min-h-[120px] resize-y rounded-md border border-gray-600 bg-white text-black px-3 py-2 text-sm outline-none"
                />
                <button
                  type="button"
                  onClick={handleAddScene}
                  disabled={isGenerating}
                  className="mt-3 w-full inline-flex items-center justify-center rounded-md bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold py-2 transition-colors"
                >
                   {isGenerating ? 'Generating...' : 'Add Scene'}
                </button>
              </section>
            </aside>
          </div>
        </div>
      </DndContext>
    </section>
  );
}

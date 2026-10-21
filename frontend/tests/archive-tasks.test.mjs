import assert from "node:assert/strict";
import { test } from "node:test";
import { loadArchiveCollection, paginateArchive } from "../src/features/tasks/archive-tasks.ts";

const tasks = [
  { id: "new-task-old-archive", archived_at: "2026-10-18T10:00:00Z" },
  { id: "old-task-new-archive", archived_at: "2026-10-20T10:00:00Z" },
  { id: "middle", archived_at: "2026-10-19T10:00:00Z" }
];

test("archive ordering spans API pages before UI pagination", async () => {
  const offsets = [];
  const collection = await loadArchiveCollection(async (offset) => {
    offsets.push(offset);
    return { items: tasks.slice(offset,offset+2), pagination: { total: 3, limit: 2, offset } };
  });
  assert.deepEqual(offsets,[0,2]);
  assert.deepEqual(paginateArchive(collection,"archived_at_desc",1,0).items.map((task) => task.id),["old-task-new-archive"]);
  assert.deepEqual(paginateArchive(collection,"archived_at_desc",1,1).items.map((task) => task.id),["middle"]);
  assert.equal(paginateArchive(collection,"archived_at_desc",1,1).pagination.total,3);
  assert.deepEqual(collection,tasks);
});

test("ascending archive order and server creation order remain available", () => {
  assert.deepEqual(paginateArchive(tasks,"archived_at_asc",20,0).items.map((task) => task.id),[tasks[0].id,tasks[2].id,tasks[1].id]);
  assert.deepEqual(paginateArchive(tasks,"created_at_desc",20,0).items,tasks);
});

test("failed archive page rejects instead of presenting incomplete results", async () => {
  await assert.rejects(loadArchiveCollection(async (offset) => {
    if (offset) throw new Error("offline");
    return { items: tasks.slice(0,2), pagination: { total: 3, limit: 2, offset: 0 } };
  }),/offline/);
});

test("an archive shrinking during loading cannot cause an endless request loop", async () => {
  let requests = 0;
  const items = await loadArchiveCollection(async (offset) => {
    requests++;
    return { items: offset ? [] : tasks.slice(0,2), pagination: { total: 3, limit: 2, offset } };
  });
  assert.equal(requests,2);
  assert.equal(items.length,2);
});

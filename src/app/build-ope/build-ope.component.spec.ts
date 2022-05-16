import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BuildOpeComponent } from './build-ope.component';

describe('BuildOpeComponent', () => {
  let component: BuildOpeComponent;
  let fixture: ComponentFixture<BuildOpeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BuildOpeComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BuildOpeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
